from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.server_config import ServerConfig
from app.models.user import User
from app.utils.ip_utils import get_server_ip
from app.utils.wg_keygen import safe_generate_keypair

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.access_token_expire_hours)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return user


def create_server_config(db: Session) -> None:
    """Auto-initialize server config on first run if not already present."""
    existing = db.query(ServerConfig).first()
    if existing:
        return

    private_key, public_key = safe_generate_keypair()
    server_address = get_server_ip(settings.subnet)
    interface = settings.wg_interface

    # iptables rules are now managed in entrypoint.sh for Docker compatibility
    # PostUp/PostDown are left empty to avoid hardcoded eth0 references
    post_up = ""
    post_down = ""

    cfg = ServerConfig(
        interface_name=interface,
        private_key=private_key,
        public_key=public_key,
        listen_port=settings.server_port,
        address=server_address,
        endpoint=settings.server_endpoint,
        post_up=post_up,
        post_down=post_down,
    )
    db.add(cfg)
    db.commit()


def create_admin_user(db: Session) -> None:
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        return
    user = User(
        username="admin",
        password_hash=hash_password(settings.admin_password),
        must_change_password=True,
        is_admin=True,
    )
    db.add(user)
    db.commit()


def create_vpn_server_peer(db: Session) -> None:
    """Create a system peer representing the VPN server itself.
    This peer cannot be deleted and is used for permission management."""
    from app.models.peer import Peer
    
    existing = db.query(Peer).filter(Peer.name == "VPN Server", Peer.is_system == True).first()
    if existing:
        return
    
    # Generate a dummy keypair (not used for actual WireGuard connections)
    private_key, public_key = safe_generate_keypair()
    
    # Assign the server's own IP from the subnet
    server_ip = get_server_ip(settings.subnet)
    
    peer = Peer(
        name="VPN Server",
        peer_type="server",
        device_type="server",
        private_key=private_key,
        public_key=public_key,
        assigned_ip=server_ip,
        tunnel_mode="split",
        persistent_keepalive=0,
        is_enabled=True,
        is_system=True,  # Mark as system peer - cannot be deleted
    )
    db.add(peer)
    db.commit()
