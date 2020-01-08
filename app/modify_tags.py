def modify_tags(response, values, tags_for_asg):
  tags = response['Tags']

  for item in values:
      test = []
      for key in item.keys():
          for tag in tags:
              if key in tag['Key']:
                  test.append({key: True})
                  if tag['Value'] != item[key]:
                      tag['Value'] = item[key]
          if not {key: True} in test:
            new_tag = {
              'Value': item[key],
              'ResourceType': 'auto-scaling-group',
              'ResourceId': response['asgName'],
              'Key': key,
              'PropagateAtLaunch': True 
            } if tags_for_asg else {
                'Value': item[key],
                'Key': key
            }

            response['Tags'].append(new_tag)

  return response
