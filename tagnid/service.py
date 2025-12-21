from .models import Registration, Vitals


def create_registration(first_name, last_name, region, majilis, dob=None):
    """
    Service function to create a new registration
    
    Args:
        first_name: First name of the person
        last_name: Last name of the person
        region: Region choice (URR, LRR, CRR, etc.)
        majilis: Majilis choice (ATAFL, Khuddam, ANSAR, GUEST)
        dob: Date of birth (optional)
    
    Returns:
        Registration object
    """
    registration = Registration.objects.create(
        first_name=first_name,
        last_name=last_name,
        region=region,
        majilis=majilis,
        dob=dob
    )
    return registration


def update_registration(registration_id, **kwargs):
    """
    Service function to update an existing registration
    
    Args:
        registration_id: ID of the registration to update
        **kwargs: Fields to update (first_name, last_name, dob, region, majilis)
    
    Returns:
        Updated Registration object
    
    Raises:
        Registration.DoesNotExist: If registration not found
    """
    try:
        registration = Registration.objects.get(id=registration_id)
        for key, value in kwargs.items():
            if hasattr(registration, key):
                setattr(registration, key, value)
        registration.save()
        return registration
    except Registration.DoesNotExist:
        raise Registration.DoesNotExist(f"Registration with id {registration_id} does not exist")


def delete_registration(registration_id):
    """
    Service function to delete a registration
    
    Args:
        registration_id: ID of the registration to delete
    
    Returns:
        True if deleted successfully
    
    Raises:
        Registration.DoesNotExist: If registration not found
    """
    try:
        registration = Registration.objects.get(id=registration_id)
        registration.delete()
        return True
    except Registration.DoesNotExist:
        raise Registration.DoesNotExist(f"Registration with id {registration_id} does not exist")


def create_vitals(registration_id, blood_group=None, height=None):
    """
    Service function to create vitals for a registration
    
    Args:
        registration_id: ID of the registration
        blood_group: Blood group (optional)
        height: Height in cm (optional)
    
    Returns:
        Vitals object
    
    Raises:
        Registration.DoesNotExist: If registration not found
    """
    try:
        registration = Registration.objects.get(id=registration_id)
        vitals = Vitals.objects.create(
            registration=registration,
            blood_group=blood_group,
            height=height
        )
        return vitals
    except Registration.DoesNotExist:
        raise Registration.DoesNotExist(f"Registration with id {registration_id} does not exist")


def update_vitals(registration_id, **kwargs):
    """
    Service function to update vitals for a registration
    
    Args:
        registration_id: ID of the registration
        **kwargs: Fields to update (blood_group, height)
    
    Returns:
        Updated Vitals object
    
    Raises:
        Registration.DoesNotExist: If registration not found
        Vitals.DoesNotExist: If vitals not found
    """
    try:
        registration = Registration.objects.get(id=registration_id)
        vitals, created = Vitals.objects.get_or_create(registration=registration)
        for key, value in kwargs.items():
            if hasattr(vitals, key):
                setattr(vitals, key, value)
        vitals.save()
        return vitals
    except Registration.DoesNotExist:
        raise Registration.DoesNotExist(f"Registration with id {registration_id} does not exist")


def delete_vitals(registration_id):
    """
    Service function to delete vitals for a registration
    
    Args:
        registration_id: ID of the registration
    
    Returns:
        True if deleted successfully
    
    Raises:
        Registration.DoesNotExist: If registration not found
        Vitals.DoesNotExist: If vitals not found
    """
    try:
        registration = Registration.objects.get(id=registration_id)
        vitals = Vitals.objects.get(registration=registration)
        vitals.delete()
        return True
    except Registration.DoesNotExist:
        raise Registration.DoesNotExist(f"Registration with id {registration_id} does not exist")
    except Vitals.DoesNotExist:
        raise Vitals.DoesNotExist(f"Vitals for registration {registration_id} does not exist")

