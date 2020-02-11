def get_backup_values(request, backup_keys):
    backup_values = []

    for key in request.keys():
      if key in backup_keys:
          new_dict = dict()
          new_dict[key] = request[key]
          backup_values.append(new_dict)

    return backup_values