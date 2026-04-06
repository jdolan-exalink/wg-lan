import re
from typing import Any

import ldap3
from ldap3 import ALL, SUBTREE
from ldap3.utils import conv as ldap_conv
from ldap3.core.exceptions import LDAPSocketOpenError, LDAPBindError

from app.config import settings
from app.models.server_config import ServerConfig


class ADAuthenticationError(Exception):
    pass


class ADConnectionError(ADAuthenticationError):
    pass


class ADInvalidCredentialsError(ADAuthenticationError):
    pass


class ADNoMembershipError(ADAuthenticationError):
    pass


def _encrypt_password(password: str) -> str:
    """Encrypt password using settings.secret_key."""
    import base64
    from cryptography.fernet import Fernet
    key_bytes = settings.secret_key.encode()[:32]
    key_bytes = key_bytes.ljust(32, b'0')
    key = base64.urlsafe_b64encode(key_bytes).decode()
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()


def _decrypt_password(encrypted: str) -> str:
    """Decrypt password using settings.secret_key."""
    import base64
    from cryptography.fernet import Fernet
    key_bytes = settings.secret_key.encode()[:32]
    key_bytes = key_bytes.ljust(32, b'0')
    key = base64.urlsafe_b64encode(key_bytes).decode()
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()


def get_ad_config(db) -> dict[str, Any] | None:
    cfg = db.query(ServerConfig).first()
    if not cfg or not cfg.ad_enabled or not cfg.ad_server:
        return None
    
    bind_password = cfg.ad_bind_password
    if bind_password:
        try:
            bind_password = _decrypt_password(bind_password)
        except Exception:
            pass
    
    return {
        "server": cfg.ad_server,
        "server_backup": cfg.ad_server_backup,
        "base_dn": cfg.ad_base_dn,
        "bind_dn": cfg.ad_bind_dn,
        "bind_password": bind_password,
        "user_filter": cfg.ad_user_filter or "(sAMAccountName={username})",
        "group_filter": cfg.ad_group_filter or "(member={user_dn})",
        "use_ssl": cfg.ad_use_ssl,
        "require_membership": cfg.ad_require_membership,
    }


def extract_cn_from_dn(dn: str) -> str:
    """Extract the CN (Common Name) from a DN string."""
    match = re.match(r"CN=([^,]+)", dn, re.IGNORECASE)
    return match.group(1) if match else dn


def _convert_bind_username_to_dn(bind_username: str, base_dn: str | None = None) -> str | None:
    r"""Convert DOMAIN\username format to LDAP DN format.
    
    Examples:
        EMPRESA\Administrador -> CN=Administrador,CN=Users,DC=empresa,DC=local
        MYDOMAIN\jsmith -> CN=jsmith,CN=Users,DC=mydomain
    
    If base_dn is provided, extracts domain from it instead.
    """
    if not bind_username or '\\' not in bind_username:
        return bind_username
    
    domain, username = bind_username.split('\\', 1)
    
    if base_dn:
        dc_parts = ','.join([f"DC={part.split('=')[1].lower()}" for part in base_dn.split(',')])
    else:
        domain_parts = domain.split('.')
        dc_parts = ','.join([f"DC={part.lower()}" for part in domain_parts])
    
    return f"CN={username},CN=Users,{dc_parts}"


def authenticate_ad_with_backup(db, username: str, password: str) -> dict[str, Any]:
    """Fallback authentication using backup AD server."""
    cfg = db.query(ServerConfig).first()
    if not cfg or not cfg.ad_enabled or not cfg.ad_server_backup:
        raise ADAuthenticationError("AD backup server is not configured")

    if not password:
        raise ADInvalidCredentialsError("Password is required")

    bind_password = cfg.ad_bind_password
    if bind_password:
        try:
            bind_password = _decrypt_password(bind_password)
        except Exception:
            pass

    server = ldap3.Server(cfg.ad_server_backup, use_ssl=cfg.ad_use_ssl, get_info=ALL)

    try:
        bind_dn = cfg.ad_bind_dn
        if bind_dn and bind_password:
            bind_dn_converted = _convert_bind_username_to_dn(bind_dn, cfg.ad_base_dn)
            admin_conn = ldap3.Connection(server, user=bind_dn_converted, password=bind_password, auto_bind=True)
        else:
            user_filter = (cfg.ad_user_filter or "(sAMAccountName={username})").format(username=ldap_conv.escape_filter_chars(username))
            search_base = cfg.ad_base_dn
            admin_conn = ldap3.Connection(server, auto_bind=True)
            admin_conn.search(search_base, f"(&{user_filter}(objectClass=user))", attributes=["sAMAccountName"])

            if not admin_conn.entries:
                raise ADInvalidCredentialsError("User not found in AD")

            user_dn = str(admin_conn.entries[0].entry_dn)
            admin_conn.unbind()

            conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)

            if not conn.bound:
                raise ADInvalidCredentialsError("Invalid credentials")

            return get_user_info(conn, {
                "server": cfg.ad_server_backup,
                "base_dn": cfg.ad_base_dn,
                "bind_dn": cfg.ad_bind_dn,
                "bind_password": bind_password,
                "user_filter": cfg.ad_user_filter or "(sAMAccountName={username})",
                "group_filter": cfg.ad_group_filter or "(member={user_dn})",
                "use_ssl": cfg.ad_use_ssl,
                "require_membership": cfg.ad_require_membership,
            }, username, user_dn)

        user_filter = (cfg.ad_user_filter or "(sAMAccountName={username})").format(username=ldap_conv.escape_filter_chars(username))
        search_base = cfg.ad_base_dn

        admin_conn.search(
            search_base,
            f"(&{user_filter}(objectClass=user))",
            attributes=["sAMAccountName", "memberOf"],
        )

        if not admin_conn.entries:
            raise ADInvalidCredentialsError("User not found in AD")

        user_dn = str(admin_conn.entries[0].entry_dn)
        member_of = getattr(admin_conn.entries[0], "memberOf", [])

        conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)

        if not conn.bound:
            raise ADInvalidCredentialsError("Invalid credentials")

        result = get_user_info_with_groups(conn, {
            "server": cfg.ad_server_backup,
            "base_dn": cfg.ad_base_dn,
            "bind_dn": cfg.ad_bind_dn,
            "bind_password": bind_password,
            "user_filter": cfg.ad_user_filter or "(sAMAccountName={username})",
            "group_filter": cfg.ad_group_filter or "(member={user_dn})",
            "use_ssl": cfg.ad_use_ssl,
            "require_membership": cfg.ad_require_membership,
        }, username, user_dn, member_of)
        conn.unbind()
        admin_conn.unbind()
        return result

    except LDAPSocketOpenError:
        raise ADConnectionError(f"Cannot connect to AD backup server")
    except LDAPBindError as e:
        raise ADInvalidCredentialsError(f"LDAP bind error: {e}")
    except Exception as e:
        raise ADAuthenticationError(f"AD authentication failed: {e}")


def authenticate_ad(db, username: str, password: str) -> dict[str, Any]:
    config = get_ad_config(db)
    if not config:
        raise ADAuthenticationError("AD is not configured")

    if not password:
        raise ADInvalidCredentialsError("Password is required")

    # Normalize username: strip DOMAIN\ prefix before LDAP search
    if "\\" in username:
        username = username.split("\\", 1)[1]

    server = ldap3.Server(config["server"], use_ssl=config["use_ssl"], get_info=ALL)

    try:
        bind_dn = config["bind_dn"]
        bind_password = config["bind_password"]

        if bind_dn and bind_password:
            bind_dn_converted = _convert_bind_username_to_dn(bind_dn, config.get("base_dn"))
            admin_conn = ldap3.Connection(server, user=bind_dn_converted, password=bind_password, auto_bind=True)
        else:
            user_filter = config["user_filter"].format(username=ldap_conv.escape_filter_chars(username))
            search_base = config["base_dn"]
            admin_conn = ldap3.Connection(server, auto_bind=True)
            admin_conn.search(search_base, f"(&{user_filter}(objectClass=user))", attributes=["dn", "sAMAccountName"])

            if not admin_conn.entries:
                raise ADInvalidCredentialsError("User not found in AD")

            user_dn = str(admin_conn.entries[0].entry_dn)
            sam_account_name = str(admin_conn.entries[0].sAMAccountName)
            admin_conn.unbind()

            conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)

            if not conn.bound:
                raise ADInvalidCredentialsError("Invalid credentials")

            return get_user_info(conn, config, sam_account_name, user_dn)

        user_filter = config["user_filter"].format(username=ldap_conv.escape_filter_chars(username))
        search_base = config["base_dn"]

        admin_conn.search(
            search_base,
            f"(&{user_filter}(objectClass=user))",
            attributes=["sAMAccountName", "memberOf"],
        )

        if not admin_conn.entries:
            raise ADInvalidCredentialsError("User not found in AD")

        user_dn = str(admin_conn.entries[0].entry_dn)
        sam_account_name = str(admin_conn.entries[0].sAMAccountName)
        member_of = getattr(admin_conn.entries[0], "memberOf", [])

        conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)

        if not conn.bound:
            raise ADInvalidCredentialsError("Invalid credentials")

        result = get_user_info_with_groups(conn, config, sam_account_name, user_dn, member_of)
        conn.unbind()
        admin_conn.unbind()
        return result

    except LDAPSocketOpenError as e:
        if config.get("server_backup"):
            return authenticate_ad_with_backup(db, username, password)
        raise ADConnectionError(f"Cannot connect to AD server: {e}")
    except LDAPBindError as e:
        raise ADInvalidCredentialsError(f"LDAP bind error: {e}")
    except Exception as e:
        raise ADAuthenticationError(f"AD authentication failed: {e}")


def get_user_info(conn, config, username: str, user_dn: str) -> dict[str, Any]:
    search_base = config["base_dn"]
    # Use sAMAccountName directly (already canonical, no DOMAIN\ prefix)
    user_filter = config["user_filter"].format(username=ldap_conv.escape_filter_chars(username))

    conn.search(
        search_base,
        f"(&{user_filter}(objectClass=user))",
        attributes=["sAMAccountName", "memberOf"],
    )

    if not conn.entries:
        raise ADAuthenticationError("User not found")

    entry = conn.entries[0]
    member_of = getattr(entry, "memberOf", [])
    sam_account_name = str(entry.sAMAccountName)

    return get_user_info_with_groups(conn, config, sam_account_name, user_dn, member_of)


def get_user_info_with_groups(conn, config, username: str, user_dn: str, member_of) -> dict[str, Any]:
    ad_groups = []
    if member_of:
        for group_dn in member_of:
            group_name = extract_cn_from_dn(str(group_dn))
            ad_groups.append({
                "dn": str(group_dn),
                "name": group_name,
            })

    return {
        "username": username,
        "user_dn": user_dn,
        "ad_groups": ad_groups,
    }


def get_ad_groups(db) -> list[dict]:
    import logging
    config = get_ad_config(db)
    if not config:
        return []

    server = ldap3.Server(config["server"], use_ssl=config["use_ssl"], get_info=ALL)

    try:
        bind_dn = config["bind_dn"]
        bind_password = config["bind_password"]

        if not bind_dn or not bind_password:
            return []

        bind_dn_converted = _convert_bind_username_to_dn(bind_dn, config.get("base_dn"))
        
        conn = ldap3.Connection(server, user=bind_dn_converted, password=bind_password, auto_bind=True)

        search_base = config["base_dn"]
        conn.search(
            search_base,
            "(objectClass=group)",
            SUBTREE,
        )

        groups = []
        for idx, entry in enumerate(conn.entries):
            try:
                dn = str(entry.entry_dn)
            except AttributeError:
                try:
                    dn = str(entry.dn)
                except AttributeError:
                    dn = "unknown"
            
            try:
                name = str(entry.cn)
            except AttributeError:
                name = dn
            
            try:
                sam_name = str(entry.sAMAccountName)
            except AttributeError:
                sam_name = name
            
            groups.append({
                "dn": dn,
                "name": name,
                "sam_name": sam_name,
            })
            
        logging.warning(f"Processed {len(groups)} groups successfully")
        conn.unbind()
        return groups

    except Exception as e:
        import traceback
        logging.warning(f"AD Groups error: {e}")
        traceback.print_exc()
        return []

    server = ldap3.Server(config["server"], use_ssl=config["use_ssl"], get_info=ALL)

    try:
        bind_dn = config["bind_dn"]
        bind_password = config["bind_password"]

        if not bind_dn or not bind_password:
            return []

        bind_dn_converted = _convert_bind_username_to_dn(bind_dn, config.get("base_dn"))
        
        conn = ldap3.Connection(server, user=bind_dn_converted, password=bind_password, auto_bind=True)

        search_base = config["base_dn"]
        conn.search(
            search_base,
            "(objectClass=group)",
            SUBTREE,
        )

        groups = []
        for idx, entry in enumerate(conn.entries):
            try:
                dn = str(entry.entry_dn)
            except AttributeError:
                try:
                    dn = str(entry.dn)
                except AttributeError:
                    dn = "unknown"
            
            try:
                name = str(entry.cn)
            except AttributeError:
                name = dn
            
            try:
                sam_name = str(entry.sAMAccountName)
            except AttributeError:
                sam_name = name
            
            groups.append({
                "dn": dn,
                "name": name,
                "sam_name": sam_name,
            })
            
        logging.warning(f"Processed {len(groups)} groups successfully")
        conn.unbind()
        return groups

    except Exception as e:
        import traceback
        logging.warning(f"AD Groups error: {e}")
        traceback.print_exc()
        return []


def test_ad_connection(db) -> dict[str, Any]:
    import logging
    config = get_ad_config(db)
    if not config:
        return {"success": False, "error": "AD is not configured"}

    server = ldap3.Server(config["server"], use_ssl=config["use_ssl"], get_info=ALL)

    bind_dn = config["bind_dn"]
    bind_password = config["bind_password"]

    if not bind_dn or not bind_password:
        return {"success": False, "error": "AD bind credentials not configured"}

    bind_dn_converted = _convert_bind_username_to_dn(bind_dn, config.get("base_dn"))
    
    logging.warning(f"AD Test: server={config['server']}, bind_dn={bind_dn_converted}, base_dn={config.get('base_dn')}")
    
    try:
        conn = ldap3.Connection(server, user=bind_dn_converted, password=bind_password, auto_bind=True)

        if not conn.bound:
            conn.unbind()
            return {"success": False, "error": "Failed to bind to AD"}

        conn.unbind()
        return {"success": True, "message": "Successfully connected to AD"}

    except LDAPSocketOpenError as e:
        return {"success": False, "error": f"Cannot connect to AD server: {e}"}
    except LDAPBindError as e:
        return {"success": False, "error": f"Invalid AD credentials: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {type(e).__name__}: {e}"}
