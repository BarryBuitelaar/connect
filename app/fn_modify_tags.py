def modify_tags(response: dict, tag_for_asg: bool, tag_for_aws: bool, tag_values: list, **kwargs) -> dict:
    test = []
    response = response

    for item in tag_values:
        for item_key in item.keys():
            for tag in response['Tags']:
                if item_key == tag['Key']:
                    test.append({item_key: True})
                    if tag['Value'] != item[item_key]:
                        tag['Value'] = (
                            str(item[item_key]) if tag_for_aws else item[item_key]
                        )

        if tag_for_aws or not {item_key: True} in test:
            formatted_key = str(item[item_key]) if tag_for_aws else item[item_key]
            new_tag = (
                {
                    'Value': formatted_key,
                    'ResourceType': 'auto-scaling-group',
                    'ResourceId': response['asgName'],
                    'Key': item_key,
                    'PropagateAtLaunch': True,
                }
                if tag_for_asg
                else {'Value': item_key, 'Key': 'AWSSchedule'}
            )
            response['Tags'].append(new_tag)

    return response
