#!/usr/bin/env python3
import os
import sys
import boto3

def list_accounts_in_ou(orgs_client, ou_id):
  accounts = []
  accounts_paginator = orgs_client.get_paginator('list_accounts_for_parent')

  for page in accounts_paginator.paginate(ParentId=ou_id):
    for account in page.get('Accounts'):
      accounts.append(account.get('Id'))
  return(accounts)

def get_ou_ids_recursively(orgs_client, parent_id):
  output_ou_ids = []
  paginator = orgs_client.get_paginator('list_children')
  pages  = paginator.paginate(
    ParentId=parent_id,
    ChildType='ORGANIZATIONAL_UNIT'
  )

  for page in pages:
    for ou in page.get('Children'):
      output_ou_ids.append(ou.get('Id'))
      output_ou_ids.extend(get_ou_ids_recursively(orgs_client, ou.get('Id')))
  return output_ou_ids


def list_accounts_in_ou_recursively(orgs_client, parent_id):
  output_accounts = []
  ou_ids = get_ou_ids_recursively(orgs_client, parent_id)
  ou_ids.append(parent_id)
  for ou in ou_ids:
    accounts_in_sub_ou = list_accounts_in_ou(orgs_client, ou)
    output_accounts.extend(accounts_in_sub_ou)
  return output_accounts

if __name__ == '__main__':
  orgs_client = boto3.client('organizations')
  try:
    ou_id = sys.argv[1]
    print(list_accounts_in_ou_recursively(orgs_client, ou_id))
  except IndexError as e:
    print('Usage: {0} {1}'.format(sys.argv[0], 'ou-ouid'))

def handler(event, context):
  orgs_client = boto3.client('organizations')
  try:
    ou_id = context.get('ou_id')
    return(list_accounts_in_ou_recursively(orgs_client, ou_id))
  except Exception as e:
    print(e)