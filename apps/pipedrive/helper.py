def upload_path_service_contract(instance, filename):
    return f"{instance.deal.lead.organisation_id}/service_contract/{instance.deal.lead.title}/{filename}"


def upload_path_serviceproposal(instance, filename):
    return f"{instance.prospect.lead.organisation_id}/service_proposal/{instance.prospect.lead.title}/{filename}"


def upload_path_rdcapsule(instance, filename):
    return f"rdcapsule/{instance.deal.prospect.lead.title}/{filename}"
