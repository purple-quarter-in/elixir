from apps.pipedrive.models import changelog as Changelog


def changelog(changlog_dict, old_obj, new_obj_dict, operation, user_id):
    mapping = {
        "Entity Created": {"from_to": False},
        "State Update": {"from_to": False},
        "Status Update": {"from_to": True},
        "Field Update": {"from_to": True},
    }
    for field in new_obj_dict:
        if field in changlog_dict[operation]:
            field_type = changlog_dict[operation][field]["type"]
            changed_from = None
            changed_to = None
            field_to_get = None
            if "field_to_get" in changlog_dict[operation][field]:
                field_to_get = changlog_dict[operation][field]["field_to_get"]
            if field_type in mapping and mapping[field_type]["from_to"]:
                if field_to_get and (old_obj.__getattribute__(field)):
                    changed_from = getattr((old_obj.__getattribute__(field)), field_to_get)()
                else:
                    changed_from = old_obj.__getattribute__(field)
                if field_to_get and new_obj_dict.get(field):
                    changed_to = getattr(new_obj_dict.get(field), field_to_get)()
                else:
                    changed_to = new_obj_dict.get(field)
                if changed_from == changed_to:
                    continue
            Changelog.objects.create(
                type=field_type,
                field_name=field,
                changed_to=changed_to,
                changed_from=changed_from,
                description=changlog_dict[operation][field]["description"],
                changed_by_id=user_id,
                model_name=changlog_dict["model"],
                obj_id=getattr(old_obj, changlog_dict["mapping_obj"])()
                if changlog_dict["is_mapping_obj_func"]
                else old_obj.__getattribute__(changlog_dict["mapping_obj"]),
            )
