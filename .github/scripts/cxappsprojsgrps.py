import requests
import os
import json
import uuid
import urllib.parse

cx1_tenant_name = 'mskcc'
cx1_base_url = 'https://ast.checkmarx.net/'
cx1_auth_url = cx1_base_url + 'auth/realms/' + cx1_tenant_name + '/protocol/openid-connect/token'
cx1_application_url = cx1_base_url + 'api/applications'
cx1_project_url = cx1_base_url + 'api/projects'
cx1_group_auth_url = 'https://iam.checkmarx.net/auth/realms/' + cx1_tenant_name + '/protocol/openid-connect/token'
cx1_group_url = 'https://iam.checkmarx.net/auth/admin/realms/' + cx1_tenant_name + '/groups'
cx1_client_id = os.environ['CX1_CLIENT_ID']
cx1_client_secret = os.environ['CX1_CLIENT_SECRET']
cx1_application_name = os.environ['CX1_PROJECT_TEAM_NAME']
cx1_application_id = ''
cx1_project_name = os.environ['CX1_REPO_NAME']
cx1_project_id = ''
cx1_aad_group_names = os.environ['CX1_AAD_GROUP_NAMES']
cx1_aad_group_ids = os.environ['CX1_AAD_GROUP_NAMES']
cx1_aad_group_token = os.environ['CX1_AAD_GROUP_TOKEN']
cx1_access_token = ''

class MakeApiCall:

    def get_data(self, api):

        response = requests.get(f"{api}")
        if response.status_code == 200:
            print("sucessfully fetched the data")
            self.formatted_print(response.json())
        else:
            print(
                f"Hello, there's a {response.status_code} error with your request")
            print(
                f"Error: {response.text}")

    def get_access_token(self, api, cx1_api_auth_info, cx1_api_header):
        response = requests.post(f"{api}", cx1_api_auth_info, cx1_api_header)
        if response.status_code == 200:
            print("sucessfully fetched with parameters provided")
            self.formatted_print(response.json())
        else:
            print(
                f"Hello, there's a {response.status_code} error with your request")
            print(
                f"Error: {response.text}")
            exit()

    def translate_group_names(self, cx1_group_url, cx1_aad_group_names, my_access_token):
        headers = {
            "Authorization": f"Bearer {my_access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(cx1_group_url, headers=headers)

        groups_current = [(item['name'], item['id']) for item in json.loads(response.text)]
        groups_param = cx1_aad_group_names.split(",")
        global cx1_aad_group_ids
        
        for i in groups_param:
            v_sign = 'N'
            for v in groups_current:
                if i.lower() == v[0].lower():
                    v_sign = 'Y'
                    cx1_aad_group_ids = cx1_aad_group_ids.replace( i, v[1] )
                    print(cx1_aad_group_ids)

        #cx1_aad_group_ids = cx1_aad_group_ids.replace( "%2C" , "'%2C'" )
        #values = cx1_aad_group_ids.split(',')
        #quoted_values = ['"{}"'.format(value) for value in values]
        #cx1_aad_group_ids = ','.join(quoted_values)


    def check_groups(self, cx1_group_auth_url, cx1_group_url, cx1_aad_group_names):
        group_data = {
            'grant_type': 'refresh_token',
            'client_id': 'ast-app',
            'refresh_token': cx1_aad_group_token
        }
        
        response = requests.post(cx1_group_auth_url, data=group_data)
        my_access_token = json.loads(response.text)['access_token']
        headers = {
            "Authorization": f"Bearer {my_access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(cx1_group_url, headers=headers)

        groups_current = [item['name'] for item in json.loads(response.text)]
        groups_param = cx1_aad_group_names.split(",")

        for i in groups_param:
            v_sign = 'N'
            for v in groups_current:
                if i.lower() == v.lower():
                    v_sign = 'Y'

            if v_sign == 'Y':
                print(i)
            else: 
                group_data = {
                    'name': i,
                }
                response = requests.post(cx1_group_url, headers=headers, json=group_data)
                print(response.content.decode('utf-8'))
                response = requests.get(cx1_group_url, headers=headers) 
                groups = response.json()
                for group in groups:
                    if group['name'] == i:
                        group_id = group['id']
                        break
                role_endpoint = f"{cx1_group_url}/{group_id}/role-mappings/clients/76da925a-4689-4aac-bb6c-01e66e2e4bf5"
                role_data = [{
                    'id': 'c896cc03-0ee5-44f4-9cc3-b31be800ae12',
                    'name': 'in-group-viewer',
                    'composite': True,
                    'clientRole': True,
                    'containerId': '76da925a-4689-4aac-bb6c-01e66e2e4bf5'
                }]
                response = requests.post(role_endpoint, headers=headers, json=role_data)
                if ( response.status_code == 200 or response.status_code == 204 ):
                    print("sucessfully fetched with parameters provided")
                else:
                    print(
                        f"Hello, there's a {response.status_code} error with your request")
        self.translate_group_names(cx1_group_url, cx1_aad_group_names, my_access_token)

	
    def check_projects(self, cx1_project_url, cx1_project_name, headersAuth):
        response = requests.get(cx1_project_url, headers=headersAuth)
        if response.status_code == 200:
            print("sucessfully fetched with parameters provided")
            j = response.json()
            self.formatted_print(j)

            projs = j['projects']
            for proj in projs:
                project_name = proj['name']
                project_id = proj['id']
                if project_name.lower() == cx1_project_name.lower():
                    global cx1_project_id
                    cx1_project_id = project_id

            print(cx1_aad_group_ids)
		
            if cx1_project_id == "":
                print(f"project {cx1_project_name} not found")

                project_data = {
                    'name' : cx1_project_name,
                    'groups' : [ cx1_aad_group_ids.split(',') ],
                    'repoUrl' : '',
                    'mainBranch' : '',
                    'origin' : '',
                    'criticality' : 4
		}

                print(cx1_aad_group_ids)
                print(project_data)
                response = requests.post(cx1_project_url, headers=headersAuth, data=json.dumps(project_data))
          #      response = requests.post(cx1_project_url, headers=headersAuth, json=(project_data))

                if ( response.status_code == 200 or response.status_code == 201 ):
                    print("sucessfully fetched with parameters provided")
                else:
                    print(
                        f"Hello, there's a {response.status_code} error with your request")
                    print(
                        f"Error: {response.text}")
            else:
                print(f"Project Name = {cx1_project_name}")
                print(f"Project ID =  {cx1_project_id}")
                cx1_project_url_ext = cx1_project_url + '/' + cx1_project_id
                response = requests.get(cx1_project_url_ext, headers=headersAuth)
                if ( response.status_code == 200 or response.status_code == 201 ):
                    print("sucessfully fetched with parameters provided")
                    self.formatted_print(response.json())
                    a = response.json()
                    self.formatted_print(a)
                    proj_id = a['id']
                    proj_name = a['name']
                    proj_criticality = a['criticality']
                    proj_repoUrl = a['repoUrl']
                    proj_mainBranch = a['mainBranch']
                    proj_createdAt = a['createdAt']
                    proj_updatedAt = a['updatedAt']
                    proj_applicationIds = a['applicationIds']
                    proj_tags = a['tags']
                    project_data = {
                        'id' : proj_id,
                        'name' : proj_name,
                        'createdAt' : proj_createdAt,
                        'updatedAt' : proj_updatedAt,
                        'groups' : [ cx1_aad_group_ids.split(',') ],
                        'criticality' : proj_criticality,
                        'repoUrl': proj_repoUrl,
                        'mainBranch' : proj_mainBranch,
                        'tags' : proj_tags,
                        'applicationIds' : proj_applicationIds
                    }
                    print(project_data)
                    response = requests.put(cx1_project_url_ext, headers=headersAuth, data=json.dumps(project_data))
                    if ( response.status_code == 200 or response.status_code == 204 ):
                        print("sucessfully fetched with parameters provided")
                    else:
                        print(
                            f"Hello, there's a {response.status_code} error with your request")
                        print(
                            f"Error: {response.text}")
                else:
                    print(
                        f"Hello, there's a {response.status_code} error with your request")
        else:
            print(
                f"Hello, there's a {response.status_code} error with your request")

    def check_applications(self, cx1_application_url, cx1_application_name, headersAuth):

        response = requests.get(cx1_application_url, headers=headersAuth)
        if ( response.status_code == 200 or response.status_code == 201 ):
            print("sucessfully fetched with parameters provided")
            a = response.json()
            self.formatted_print(a)

            apps = a['applications']
            for app in apps:
                application_name = app['name']
                application_id = app['id']
                if application_name.lower() == cx1_application_name.lower():
                    global cx1_application_id
                    cx1_application_id = application_id
            
            if cx1_application_id == "":
                print(f"application {cx1_application_name} not found")
                application_data = {
                    'name' : cx1_application_name,
                    'description' : cx1_application_name,
                    'criticality' : 4,
                    'rules' : [
                        {
                            'type' : 'project.name.contains',
                            'value' : cx1_project_name
                        }
                    ],
                    'tags' : {
                        'priority' : 'high'
                    }
                }
                response = requests.post(cx1_application_url, headers=headersAuth, json=application_data)
                if ( response.status_code == 200 or response.status_code == 201 ):
                    print("sucessfully fetched with parameters provided")
                else:
                    print(
                        f"Hello, there's a {response.status_code} error with your request")
                    print(
                        f"Error: {response.text}")
            else:
                print(f"Application Name = {cx1_application_name}")
                print(f"Application ID =  {cx1_application_id}")
                application_data = {
                    'type' : 'project.name.contains',
                    'value' : cx1_project_name
                }
                cx1_application_update_rules_url = cx1_application_url + '/' + cx1_application_id + '/project-rules'
                response = requests.post(cx1_application_update_rules_url, headers=headersAuth, json=application_data)
                if ( response.status_code == 200 or response.status_code == 201 or response.status_code == 500 ):
                    print("sucessfully fetched with parameters provided")
                else:
                    print(
                        f"Hello, there's a {response.status_code} error with your request")
                    print(
                        f"Error: {response.text}")
        else:
            print(
                f"Hello, there's a {response.status_code} error with your request")
            print(
                f"Error: {response.text}")

    def formatted_variables(self):
        y_sign = 'N'
        if cx1_client_id == "":
            y_sign = 'Y'
        if cx1_client_secret == "":
            y_sign = 'Y'
        if cx1_application_name == "":
            y_sign = 'Y'
        if cx1_project_name == "":
            y_sign = 'Y'
        if cx1_aad_group_names == "":
            y_sign = 'Y'
        if cx1_aad_group_token == "":
            y_sign = 'Y'
        if y_sign == 'Y':
            print('Incorrect Cx-One variables provided.')
            exit()

    def formatted_print(self, obj):
        text = json.dumps(obj, sort_keys=True, indent=4)
        for key, value in obj.items():
            if key == 'access_token':
                global cx1_access_token
                cx1_access_token = value

    def __init__(self, api):
        # self.get_data(api)

        cx1_api_header = 'Content-Type: application/x-www-form-urlencoded ' + 'Accept: application/json' 
        cx1_api_auth_info = {'client_id' : cx1_client_id,
                'grant_type' : 'client_credentials',
                'client_secret' : cx1_client_secret,
        }

        self.formatted_variables()
        self.get_access_token(api, cx1_api_auth_info, cx1_api_header)
        self.check_groups(cx1_group_auth_url, cx1_group_url, cx1_aad_group_names)

        headersAuth = {
                'Accept': 'application/json; version=1.0',
                'Content-Type': 'application/json; version=1.0',
                'CorrelationId': '',
                'Authorization': 'Bearer '+ str(cx1_access_token)
        }
		
        self.check_projects(cx1_project_url, cx1_project_name, headersAuth)

        self.check_applications(cx1_application_url, cx1_application_name, headersAuth)

if __name__ == "__main__":
    api_call = MakeApiCall(cx1_auth_url)
