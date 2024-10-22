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

    def create_group_sets(self, group_sets):
        """
        Creates multiple group sets in the specified Canvas course.
    
        Args:
            group_sets (list of str): A list of group set names to be created.
    
        Returns:
            None
        """
        url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/group_categories"
    
        for category_name in group_sets:
            data = {"name": category_name}
            response = requests.post(url, headers=self.headers, json=data)
    
            # Handle both 200 (OK) and 201 (Created) status codes
            if response.status_code in [200, 201]:
                print(f"Group category '{category_name}' created successfully.")
            else:
                print(f"Failed to create group category '{category_name}': {response.status_code}, {response.text}")

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
    
    def create_groups_in_sets(self, group_set_ids, group_names):
        """
        Creates groups under multiple specified group sets based on a provided list, avoiding duplicate group names.
    
        Args:
            group_set_ids (list of int): A list of IDs of the group sets in which to create the groups.
            group_names (list of str): A list of group names to create.
    
        Returns:
            dict: A dictionary where the key is the group set ID, and the value is a list of created groups' information.
        """
        all_created_groups = {}
    
        for group_set_id in group_set_ids:
            # Fetch existing group names in the current group set to avoid duplicates
            existing_group_names = self.get_groups_in_set(group_set_id)
    
            created_groups = []
            for group_name in group_names:
                if group_name in existing_group_names:
                    print(f"Group '{group_name}' already exists in group set {group_set_id}, skipping creation.")
                    continue
    
                # Create the group if it doesn't exist
                url = f"{self.canvas_domain}/api/v1/group_categories/{group_set_id}/groups"
                data = {"name": group_name}
                create_response = requests.post(url, headers=self.headers, json=data)
                if create_response.status_code in [200, 201]:
                    print(f"Group '{group_name}' created successfully in group set {group_set_id}.")
                    created_groups.append(create_response.json())
                else:
                    print(f"Failed to create group '{group_name}' in group set {group_set_id}: {create_response.status_code}, {create_response.text}")
    
            # Store the created groups for this group set ID
            all_created_groups[group_set_id] = [{'name': group['name'], 'id': group['id']} for group in created_groups]
    
        return all_created_groups

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

############################################### Assiging Students to Groups ###############################################

    def get_all_groups(self, group_set_dict):
        """
        Fetches all groups for each group set and returns a nested dictionary mapping group set names to group names and their IDs.
    
        Args:
            group_set_dict (dict): A dictionary mapping group set names to group set IDs.
                                   Example: {'Tuesday 10-1': 12345, 'Tuesday 2-5': 67890}
    
        Returns:
            dict: A nested dictionary mapping group set names to group names and their IDs.
                  Example: {'Tuesday 10-1': {'Lab 1': 101, 'Lab 2': 102}, ...}
        """
        groups_dict = {}
    
        for group_set_name, group_set_id in group_set_dict.items():
            # Fetch all groups in the current group set
            url = f"{self.canvas_domain}/api/v1/group_categories/{group_set_id}/groups"
            response = requests.get(url, headers=self.headers)
    
            if response.status_code != 200:
                print(f"Failed to fetch groups for group set '{group_set_name}': {response.status_code}, {response.text}")
                continue
    
            groups = response.json()
            groups_dict[group_set_name] = {group['name']: group['id'] for group in groups}
    
        return groups_dict

    def assign_students_to_groups(self, student_groups, group_set_mapping, group_mapping):
        """
        Assigns students to groups in specified group sets based on a DataFrame.
    
        Args:
            student_groups (pd.DataFrame): DataFrame with columns 'id', 'name', and group sets (like 'Tuesday 10-1').
            group_set_mapping (dict): A dictionary mapping group set names to Canvas group set IDs.
                                      Example: {'Tuesday 10-1': 12345, 'Tuesday 2-5': 67890}
            group_mapping (dict): A nested dictionary mapping group set names to another dictionary
                                  of group names and Canvas group IDs.
                                  Example: {'Tuesday 10-1': {'Lab 1': 111, 'Lab 2': 222}, ...}
    
        Returns:
            None
        """
        for index, row in student_groups.iterrows():
            student_id = row['id']
            for group_set in group_set_mapping.keys():
                # Get the group name the student belongs to for this group set
                group_name = row[group_set]
    
                # Get the group set ID and group ID
                group_set_id = group_set_mapping[group_set]
                group_id = group_mapping[group_set].get(group_name)
    
                if not group_id:
                    print(f"Group '{group_name}' not found in group set '{group_set}'")
                    continue
    
                # Assign the student to the group using Canvas API
                url = f"{self.canvas_domain}/api/v1/groups/{group_id}/memberships"
                data = {"user_id": student_id}
                response = requests.post(url, headers=self.headers, json=data)
    
                if response.status_code == 200:
                    print(f"Student {row['name']} (ID: {student_id}) successfully assigned to '{group_name}' in '{group_set}'")
                else:
                    print(f"Failed to assign Student {row['name']} (ID: {student_id}) to '{group_name}' in '{group_set}': {response.status_code}, {response.text}")
