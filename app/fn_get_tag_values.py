def get_tag_values(request, tag_values):
    values = []

    for key in request.keys():
      if key in tag_values:
          new_dict = dict()
          new_dict[key] = request[key]
          values.append(new_dict)

    return values