from sqlalchemy.orm import Session

from app.models.group import ADGroupMapping, PeerGroup


def map_ad_groups_to_netloom(db: Session, ad_groups: list[dict]) -> list[PeerGroup]:
    """
    Map AD groups to NetLoom groups based on configured mappings.
    
    Args:
        db: Database session
        ad_groups: List of AD groups (with 'dn' and 'name' keys)
    
    Returns:
        List of PeerGroup objects that the user belongs to
    """
    mapped_groups = []
    
    for ad_group in ad_groups:
        mapping = (
            db.query(ADGroupMapping)
            .filter(
                ADGroupMapping.ad_group_dn == ad_group["dn"],
                ADGroupMapping.enabled == True,
            )
            .first()
        )
        
        if mapping:
            group = db.query(PeerGroup).filter(PeerGroup.id == mapping.netloom_group_id).first()
            if group and group.is_active:
                mapped_groups.append(group)
        else:
            mapping_by_name = (
                db.query(ADGroupMapping)
                .filter(
                    ADGroupMapping.ad_group_name == ad_group["name"],
                    ADGroupMapping.enabled == True,
                )
                .first()
            )
            
            if mapping_by_name:
                group = db.query(PeerGroup).filter(PeerGroup.id == mapping_by_name.netloom_group_id).first()
                if group and group.is_active:
                    mapped_groups.append(group)
    
    return mapped_groups


def get_ad_group_mappings(db: Session) -> list[ADGroupMapping]:
    return db.query(ADGroupMapping).order_by(ADGroupMapping.priority.desc()).all()


def get_ad_group_mapping(db: Session, mapping_id: int) -> ADGroupMapping | None:
    return db.query(ADGroupMapping).filter(ADGroupMapping.id == mapping_id).first()


def create_ad_group_mapping(
    db: Session,
    ad_group_dn: str,
    ad_group_name: str,
    netloom_group_id: int,
    enabled: bool = True,
    priority: int = 0,
) -> ADGroupMapping:
    existing = (
        db.query(ADGroupMapping)
        .filter(ADGroupMapping.ad_group_dn == ad_group_dn)
        .first()
    )
    
    if existing:
        existing.netloom_group_id = netloom_group_id
        existing.ad_group_name = ad_group_name
        existing.enabled = enabled
        existing.priority = priority
        db.commit()
        db.refresh(existing)
        return existing
    
    mapping = ADGroupMapping(
        ad_group_dn=ad_group_dn,
        ad_group_name=ad_group_name,
        netloom_group_id=netloom_group_id,
        enabled=enabled,
        priority=priority,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


def update_ad_group_mapping(
    db: Session,
    mapping_id: int,
    netloom_group_id: int | None = None,
    enabled: bool | None = None,
    priority: int | None = None,
) -> ADGroupMapping | None:
    mapping = get_ad_group_mapping(db, mapping_id)
    if not mapping:
        return None
    
    if netloom_group_id is not None:
        mapping.netloom_group_id = netloom_group_id
    if enabled is not None:
        mapping.enabled = enabled
    if priority is not None:
        mapping.priority = priority
    
    db.commit()
    db.refresh(mapping)
    return mapping


def delete_ad_group_mapping(db: Session, mapping_id: int) -> bool:
    mapping = get_ad_group_mapping(db, mapping_id)
    if not mapping:
        return False
    
    db.delete(mapping)
    db.commit()
    return True


def bulk_create_ad_group_mappings(
    db: Session,
    mappings: list[dict],
) -> list[ADGroupMapping]:
    created = []
    for m in mappings:
        mapping = create_ad_group_mapping(
            db,
            ad_group_dn=m["ad_group_dn"],
            ad_group_name=m["ad_group_name"],
            netloom_group_id=m["netloom_group_id"],
            enabled=m.get("enabled", True),
            priority=m.get("priority", 0),
        )
        created.append(mapping)
    return created
