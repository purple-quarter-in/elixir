def upload_path_service_contract(instance, filename):
    return f"service_contract/{instance.prospect.lead.title}/{filename}"


def upload_path_rdcapsule(instance, filename):
    return f"rdcapsule/{instance.deal.prospect.lead.title}/{filename}"
