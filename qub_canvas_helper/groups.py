import pandas as pd
import requests

class CanvasGroupManager:
    def __init__(self, canvas_domain, access_token, course_id):
        """
        Initializes the CanvasGroupManager with necessary API details.

        Args:
            canvas_domain (str): The base Canvas domain (e.g., https://yourinstitution.instructure.com).
            access_token (str): The API access token.
            course_id (int): The ID of the Canvas course.
        """
        self.canvas_domain = canvas_domain
        self.access_token = access_token
        self.course_id = course_id
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def create_group_set(self, category_name):
        """
        Creates a group category in the specified Canvas course.
    
        Args:
            category_name (str): The name of the group category to be created.
    
        Returns:
            dict: The created group category's information.
        """
        url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/group_categories"
        data = {
            "name": category_name
        }
        response = requests.post(url, headers=self.headers, json=data)
    
        # Handle both 200 (OK) and 201 (Created) status codes
        if response.status_code in [200, 201]:
            print(f"Group category '{category_name}' created successfully.")
            return response.json()
        else:
            raise Exception(f"Failed to create group category: {response.status_code}, {response.text}")

    def get_all_group_sets(self):
        """
        Fetches all group sets for the specified Canvas course (module).
    
        Returns:
            pd.DataFrame: A DataFrame containing details of all group sets in the course.
        
        Raises:
            Exception: If the API request fails.
        """
        url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/group_categories"
        
        response = requests.get(url, headers=self.headers)
    
        if response.status_code != 200:
            raise Exception(f"Failed to fetch group sets: {response.status_code}, {response.text}")
    
        # Parse the response JSON
        group_sets = response.json()
    
        # Convert the list of group sets to a DataFrame for easy handling
        df_group_sets = pd.DataFrame(group_sets)
    
        # Display the DataFrame
        return df_group_sets
    
    def get_groups_in_set(self, group_set_id):
        """
        Fetches all groups within the specified group set.
    
        Args:
            group_set_id (int): The ID of the group set to fetch groups from.
    
        Returns:
            list: A list of existing group names.
        
        Raises:
            Exception: If the API request fails.
        """
        url = f"{self.canvas_domain}/api/v1/group_categories/{group_set_id}/groups"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch existing groups: {response.status_code}, {response.text}")
    
        existing_groups = response.json()
        return [group['name'] for group in existing_groups]
    
    
    def create_groups_in_set(self, group_set_id, group_names):
        """
        Creates groups under the specified group set based on a provided list, avoiding duplicate group names.
    
        Args:
            group_set_id (int): The ID of the group set in which to create the groups.
            group_names (list of str): A list of group names to create.
    
        Returns:
            list: A list of dictionaries with information about the created groups.
        """
        # Fetch existing group names in the group set to avoid duplicates
        existing_group_names = self.get_groups_in_set(group_set_id)
    
        created_groups = []
        for group_name in group_names:
            if group_name in existing_group_names:
                print(f"Group '{group_name}' already exists, skipping creation.")
                continue
            
            # Create the group if it doesn't exist
            url = f"{self.canvas_domain}/api/v1/group_categories/{group_set_id}/groups"
            data = {"name": group_name}
            create_response = requests.post(url, headers=self.headers, json=data)
            if create_response.status_code in [200, 201]:
                print(f"Group '{group_name}' created successfully.")
                created_groups.append(create_response.json())
            else:
                print(f"Failed to create group '{group_name}': {create_response.status_code}, {create_response.text}")
            
        # Optionally, return only the group names and IDs, not the full JSON
        return [{'name': group['name'], 'id': group['id']} for group in created_groups]


    def delete_all_groups_in_set(self, group_set_id):
        """
        Deletes all groups within a specified group set in the Canvas course.
    
        Args:
            group_set_id (int): The ID of the group set to delete all groups from.
    
        Returns:
            None
        """
        # Fetch existing groups in the group set
        existing_groups = self.get_groups_in_set(group_set_id)
    
        # Iterate through each group and delete it
        for group_name in existing_groups:
            # Fetch group details to get the group ID
            url = f"{self.canvas_domain}/api/v1/group_categories/{group_set_id}/groups"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                print(f"Failed to fetch group '{group_name}': {response.status_code}, {response.text}")
                continue
            
            groups = response.json()
            for group in groups:
                if group['name'] == group_name:
                    group_id = group['id']
                    delete_url = f"{self.canvas_domain}/api/v1/groups/{group_id}"
                    delete_response = requests.delete(delete_url, headers=self.headers)
                    if delete_response.status_code == 200:
                        print(f"Successfully deleted group '{group_name}' (ID: {group_id})")
                    else:
                        print(f"Failed to delete group '{group_name}' (ID: {group_id}). Response: {delete_response.status_code}, {delete_response.text}")

