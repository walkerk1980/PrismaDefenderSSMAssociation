#!/usr/bin/env python3
import json
import requests
import boto3

def get_token(access_key_id: str, secret_key: str, console_url: str):

    authenticate_url = 'https://' + console_url + '/api/v1/authenticate'

    creds = {
        "username": access_key_id,
        "password": secret_key
    }

    headers = {}
    headers.update({"Content-Type": "application/json"})

    response = requests.post(authenticate_url, headers=headers, json=creds)

    token_json = json.loads(response.text)
    token = token_json.get('token')
    return token

def get_secret(secret_name: str, secret_version_stage: str):
    sm = boto3.client('secretsmanager')
    return json.loads(sm.get_secret_value(
        SecretId=secret_name,
        VersionStage=secret_version_stage
    ).get('SecretString'))

def put_secret(secret_name: str, secret_version_stage: str, secret_string: str):
    sm = boto3.client('secretsmanager')
    sm.put_secret_value(
        SecretId=secret_name,
        VersionStages=[secret_version_stage],
        SecretString=secret_string
    )

def handler(event, context):
    API_SECRET_NAME = 'prod/service_account/prisma_defender'
    TOKEN_SECRET_NAME = 'prod/service_account/prisma_defender_token'
    TOKEN_SECRET_VERSION = 'AWSCURRENT'
    secret = get_secret(
        secret_name=API_SECRET_NAME,
        secret_version_stage='AWSCURRENT'
    )
    console_url = secret.get('console_url')
    access_key_id = secret.get('access_key_id')
    secret_key = secret.get('secret_key')

    prisma_token = get_token(
        console_url=console_url,
        access_key_id=access_key_id,
        secret_key=secret_key
    )

    put_secret(
        secret_name=TOKEN_SECRET_NAME,
        secret_version_stage=TOKEN_SECRET_VERSION,
        secret_string='{{"console_url":"{0}", "token": "{1}"}}'.format(console_url, prisma_token)
    )

    return 'updated Secret Version Stage: TOKEN'