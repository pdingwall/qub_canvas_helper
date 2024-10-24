import pandas as pd
import requests
from datetime import datetime, timedelta

class CanvasAssignmentManager:
	
    """
    A class to handle assignment-related tasks for a Canvas course, including
    assigning students to specific assignments and checking enrollments.

    Attributes:
        course_id (int): The ID of the Canvas course.
        assignment_dict (dict): A dictionary mapping assignment codes in the uploaded(e.g., 'P1') to Canvas assignment IDs.
    """
	
    def __init__(self, canvas_domain, access_token, course_id):
        """
        Initializes the Assignments class with the course ID and assignment dictionary.
    
        Args:
            canvas_domain (str): The Canvas domain URL (here will be "https://qub.instructure.com").
            access_token (str): The access token for Canvas API.
            course_id (int): The ID of the Canvas course.
        """
        self.canvas_domain = canvas_domain
        self.access_token = access_token
        self.course_id = course_id
    
    def get_students_in_module(self):
        """
        Fetches all students enrolled in a specific Canvas module and returns their information in a DataFrame.
    
        Args:
            course_id (int): The ID of the Canvas module.
    
        Returns:
            pd.DataFrame: A DataFrame containing information about each enrolled student,
                          including 'id', 'name', 'email', and 'status'.
    
        Raises:
            Exception: If the API request to Canvas fails.
        """
        url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/enrollments"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        ########## TO DO ############
        # Filter by enrollment_state and course_section_id, will speed thing up but the below does not seem to work.
        
        params = {
            "per_page": 100,  # Fetch 100 items per page
            "type[]": "StudentEnrollment",  # Filter for only student enrollments
            #"enrollment_state": "active" # This doesn't work
            #"course_section_id": 61800 # Assume this is LT01? Could also be 61811, 67192, 67193. 67668 is definitely exam only.
        }
        
        enrollments = []
        while url:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch enrollments: {response.status_code}, {response.text}")
        
            # Add the current page of enrollments to the list
            enrollments.extend(response.json())
        
            # Check for the "next" page in the Link header
            if 'Link' in response.headers and 'rel="next"' in response.headers['Link']:
                links = response.headers['Link'].split(',')
                next_link = [link for link in links if 'rel="next"' in link]
                if next_link:
                    url = next_link[0].split(';')[0].strip('<>')
                else:
                    url = None  # No more pages
            else:
                url = None  # No more pages
        
        # Convert the list of enrollments to a DataFrame
        df_enrollments = pd.DataFrame(enrollments)
        
        # Will not filter on fetch, so remove inactive students here
        df_enrollments = df_enrollments[df_enrollments['enrollment_state'] != 'inactive']
        
        # Filter only relevant columns (e.g., student name, email, ID)
        if not df_enrollments.empty:
            df_enrollments = df_enrollments[['user', 'enrollment_state']].apply(lambda x: pd.Series(x['user']), axis=1)
        
        # Each student will have multiple entries due to different sections (LT01, PRV, TT01, WSV)
        df_enrollments = df_enrollments.drop_duplicates(subset='sis_user_id').reset_index(drop = True)
        
        return df_enrollments
    
    def check_student_enrollment(self, df_students):
        """
        Compares students in the Canvas module to the list of students in the provided DataFrame (from Excel).
        Prints discrepancies in 'sis_user_id' and includes the corresponding names.
    
        Args:
            df_students (pd.DataFrame): DataFrame containing student data from Excel (with 'sis_user_id' in the first column and 'name' in the second column).
    
        Prints:
            A message indicating whether all students are accounted for or if there are discrepancies, along with missing student names.
        """
        # Fetch students from the Canvas module using get_students_in_module
        df_canvas_students = self.get_students_in_module()
    
        # Ensure 'sis_user_id' and 'sortable_name' are present in the Canvas data
        df_canvas_students = df_canvas_students[['sis_user_id', 'sortable_name']].drop_duplicates()
    
        # Ensure 'sis_user_id' and 'name' are present in the Excel data (assuming first column is 'sis_user_id' and second column is 'name')
        df_excel_students = df_students.iloc[:, [0, 1]].drop_duplicates()
    
        # Convert both 'sis_user_id' columns to strings explicitly
        df_canvas_students['sis_user_id'] = df_canvas_students['sis_user_id'].astype(str)
        df_excel_students.iloc[:, 0] = df_excel_students.iloc[:, 0].apply(str)
    
        # Find students missing from Canvas (those present in Excel but not in Canvas)
        missing_in_canvas = df_excel_students[~df_excel_students.iloc[:, 0].isin(df_canvas_students['sis_user_id'])]
    
        # Find students missing from Excel (those present in Canvas but not in Excel)
        missing_in_excel = df_canvas_students[~df_canvas_students['sis_user_id'].isin(df_excel_students.iloc[:, 0])]
    
        # Output the result
        if missing_in_canvas.empty and missing_in_excel.empty:
            print("All students are accounted for.")
        else:
            if not missing_in_canvas.empty:
                print("Students missing in Canvas:")
                for row in missing_in_canvas.values:
                    print(f"- {row[1]} (ID: {row[0]})")
    
            if not missing_in_excel.empty:
                print("Students missing in Excel:")
                for _, row in missing_in_excel.iterrows():
                    print(f"- {row['sortable_name']} (ID: {row['sis_user_id']})")

    
    def get_assignments_in_module(self, published_status="all"):
        """
        Fetches all assignments for a specific Canvas module and returns the data in a Pandas DataFrame.
        
        Args:
            published_status (str): Filter assignments by 'all', 'published', or 'unpublished'.
                                    Default is 'all'.
        
        Returns:
            pd.DataFrame: A DataFrame containing assignment data, including 'id' and 'name' (assignment title) 
                          as the first two columns, along with any other relevant assignment data.
        
        Raises:
            Exception: If the API request to Canvas fails.
        """
        # API endpoint to get the assignments for the course
        url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/assignments"
        
        # Set up headers with the token
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        assignments = []
        
        while url:
            # Send the GET request to fetch assignments
            response = requests.get(url, headers=headers)
            
            # Check if the request was successful
            if response.status_code != 200:
                raise Exception(f"Failed to fetch assignments: {response.status_code}, {response.text}")
            
            # Add the assignments from the current page to the list
            assignments.extend(response.json())
            
            # Check for the "next" page in the Link header and update the URL
            if 'Link' in response.headers and 'rel="next"' in response.headers['Link']:
                links = response.headers['Link'].split(',')
                next_link = [link for link in links if 'rel="next"' in link]
                if next_link:
                    url = next_link[0].split(';')[0].strip('<>')
                else:
                    url = None  # No more pages
            else:
                url = None  # No more pages
        
        # Convert the list of assignments to a DataFrame
        df_assignments = pd.DataFrame(assignments)
        
        # Filter by published status if specified
        if not df_assignments.empty:
            df_assignments = df_assignments[['id', 'name', 'due_at', 'points_possible', 'published']]
            
            # Apply the filter for published status
            if published_status == "published":
                df_assignments = df_assignments[df_assignments['published'] == True]
            elif published_status == "unpublished":
                df_assignments = df_assignments[df_assignments['published'] == False]
    
        return df_assignments

    def remove_student_assignments(self, assignment_ids):
        """
        Removes student assignment overrides for one or more specified assignments in the Canvas course.
        
        Args:
            assignment_ids (list[int]): A list of assignment IDs to remove student overrides from.
    
        Raises:
            Exception: If the API request fails.
        """
        for assignment_id in assignment_ids:
            # Fetch overrides for the assignment
            url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/assignments/{assignment_id}/overrides"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
    
            # Send GET request to fetch the assignment overrides
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch assignment overrides for assignment {assignment_id}: {response.text}")
            
            # Parse the response to get a list of overrides
            overrides = response.json()
    
            # Loop through each override and delete it
            for override in overrides:
                override_id = override['id']
                delete_url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/assignments/{assignment_id}/overrides/{override_id}"
                
                # Send DELETE request to remove the override
                delete_response = requests.delete(delete_url, headers=headers)
                
                if delete_response.status_code == 200:
                    print(f"Successfully removed assignment {assignment_id} for override {override_id}.")
                else:
                    raise Exception(f"Failed to remove override {override_id} for assignment {assignment_id}: {delete_response.text}")
    
        print(f"Completed removing overrides for assignments: {assignment_ids}")
		    
    def assign_students_to_assignments(self, df_students, assignment_dict, check_enrollment=True):
        """
        Assign students to assignments based on the provided DataFrame and assignment dictionary.
        
        This function first calls `check_student_enrollment` to ensure all students in the DataFrame are enrolled in the
        Canvas module. If all students are accounted for, it proceeds with the assignment. Otherwise, it stops execution
        and outputs the result of `check_student_enrollment`. You can optionally disable this check.
    
        Args:
            df_students (pd.DataFrame): DataFrame containing student information, including assignment codes and due dates.
            check_enrollment (bool): Whether to check student enrollment before assigning (default is True).
    
        Raises:
            ValueError: If the student or assignment data is invalid or if `check_student_enrollment` identifies discrepancies.
        """
        # If enrollment check is enabled, call check_student_enrollment
        if check_enrollment:
            enrollment_check_result = self.check_student_enrollment(df_students)
            
            if enrollment_check_result != "All students are accounted for.":
                # If the enrollment check fails, print the result and stop execution
                print(enrollment_check_result)
                return

        # Canvas uses 'id' no 'sis_user_id' during override, so this will need to be changed
        # Fetch students from Canvas to get the mapping of 'sis_user_id' to Canvas 'id'
        df_canvas_students = self.get_students_in_module()

        # Create a dictionary where 'sis_user_id' is the key and 'id' is the value
        df_canvas_students['sis_user_id'] = df_canvas_students['sis_user_id'].astype("int64")
        id_mapping_dict = df_canvas_students.set_index('sis_user_id')['id'].to_dict()

        # Map the id values
        df_students['id'] = df_students['id'].map(id_mapping_dict)
        df_students.fillna(100, inplace = True) # JSON does not handle NaN and we will get NaN if there are students in excel but not on Canvas
        df_students['id'] = df_students['id'].astype("int64") # must be int not float
        
        ######################## TO CHANGE ############################### THIS IS PROBLEMATIC!!!! ######################################
        # Proceed with assigning students to assignments if enrollment is fine or the check is disabled
        assignment_columns = df_students.columns[2:]  # Assuming first two columns are student info, which they might not be!
    
        for _, row in df_students.iterrows():
            student_id = row['id']  # The student ID
            student_name = row['name']  # The student name
    
            for assignment_due_date in assignment_columns:
                assignment_code = row[assignment_due_date]  # The assignment code (e.g., P1, P2)
                assignment_id = assignment_dict.get(assignment_code)
    
                if assignment_id:
                    self.assign_assignment_to_student(student_id, student_name, assignment_id, assignment_due_date)
    
    def assign_assignment_to_student(self, student_id, student_name, assignment_id, due_date):
        """
        Create an assignment override for a specific student and set the due date.
    
        Args:
            student_id (int): The ID of the student.
            student_name (str): The name of the student.
            assignment_id (int): The Canvas assignment ID.
            due_date (str): The due date for the assignment, in ISO 8601 format.
    
        Raises:
            Exception: If the API call fails, including the student's name and ID in the error message.
        """
        url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/assignments/{assignment_id}/overrides"
    
        data = {
            "assignment_override": {
                "student_ids": [student_id],  # Assign the assignment to this specific student
                "due_at": pd.to_datetime(due_date).isoformat()  # Format the due date to ISO format
            }
        }
    
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
        # Send a POST request to create the override
        response = requests.post(url, headers=headers, json=data)
    
        # Check the response and print appropriate success or failure messages
        if response.status_code in [200, 201]:  # Check for successful responses
            print(f"Assignment {assignment_id} successfully assigned to student {student_name} ({student_id}) with due date {due_date}")
        else:
            # Print error message only if the status code indicates an error
            print(f"Failed to assign assignment {assignment_id} to student {student_name} ({student_id}). Response: {response.json()}")

    def check_student_assignment_completions(self, assignment_dict):
        """
        Checks if any students in the module are not assigned to the given assignments.
    
        Args:
            assignment_dict (dict): A dictionary mapping assignment names to Canvas assignment IDs.
    
        Returns:
            None: Prints out students not assigned to each assignment.
        """
        # Step 1: Get all students in the module
        df_students = self.get_students_in_module()
    
        # Step 2: Loop through each assignment in the dictionary
        for assignment_name, assignment_id in assignment_dict.items():
            # API endpoint to get the list of students assigned to the assignment
            url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/assignments/{assignment_id}/overrides"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
    
            # Send the GET request to fetch assignment overrides
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"Failed to fetch assignment overrides for '{assignment_name}' (ID: {assignment_id}). Response: {response.text}")
                continue
    
            # Parse the JSON response
            overrides = response.json()
    
            # Extract the list of student Canvas IDs assigned to this assignment
            assigned_student_ids = set()
            for override in overrides:
                student_ids = override.get('student_ids', [])
                assigned_student_ids.update(student_ids)
    
            # Step 3: Identify students not assigned to the current assignment
            unassigned_students = df_students[~df_students['id'].isin(assigned_student_ids)]
    
            # Step 4: Print out unassigned students for the current assignment
            if not unassigned_students.empty:
                for _, row in unassigned_students.iterrows():
                    print(f'Student {row["name"]} (ID: {row["id"]}) is not assigned to {assignment_name} (ID: {assignment_id}).')
            else:
                print(f'All students are assigned to {assignment_name} (ID: {assignment_id}).')
    
########################################################## Below are function to work with groups #########################################################

    def assign_assignments_to_group_sets(self, assignment_ids, assignments_dict, practicals_and_postlabs_dict, groups_dict, custom_practical_dates, submission_length_days):
        """
        Assigns each specified assignment to the correct group within the group set with "Assign grades to each student individually" option ticked,
        based on the provided custom practical dates and submission length.
    
        Args:
            assignment_ids (list): List of assignment IDs to be assigned to groups.
            assignments_dict (dict): A dictionary mapping assignment names to Canvas assignment IDs.
            practicals_and_postlabs_dict (dict): A dictionary mapping lab group names to post-lab assignment names.
            groups_dict (dict): A dictionary mapping lab group names to their corresponding group names and IDs.
            custom_practical_dates (pd.DataFrame): DataFrame containing practicals and their associated groups on different dates.
            submission_length_days (int): Number of days between the practical date and the assignment submission date.
    
        Returns:
            None
        """
        # Define headers inside the function
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
        # Loop through each assignment ID
        for assignment_id in assignment_ids:
            # Step 1: Find the corresponding assignment name
            assignment_name = next((name for name, id in assignments_dict.items() if id == assignment_id), None)
            if not assignment_name:
                print(f"Assignment ID {assignment_id} not found in assignments_dict.")
                continue
    
            # Step 2: Get the practical name and corresponding lab group from practicals_and_postlabs_dict
            practical_name = next((practical for practical, post_lab in practicals_and_postlabs_dict.items() if post_lab == assignment_name), None)
            if not practical_name:
                print(f"Practical not found for assignment '{assignment_name}'.")
                continue
    
            # Step 3: Loop through the columns in custom_practical_dates to assign based on date
            for date_col in custom_practical_dates.columns[1:]:
                # Find the group assigned to the current practical for the specific date
                group_name = custom_practical_dates.loc[custom_practical_dates['Practical'] == practical_name, date_col].values[0]
    
                # Calculate the submission date as `submission_length_days` days after the practical date
                practical_date = pd.to_datetime(date_col)
                submission_date = practical_date + pd.Timedelta(days=submission_length_days)
    
                # Step 4: Find the matching group ID from groups_dict
                group_id = groups_dict.get(practical_name, {}).get(group_name, None)
                if not group_id:
                    print(f"Group '{group_name}' not found for practical '{practical_name}'.")
                    continue
    
                # Step 5: Create an assignment override with the calculated submission date
                data = {
                    "assignment_override": {
                        "group_id": group_id,
                        "due_at": submission_date.isoformat(),
                        "assign_to_individuals": False  # To assign grades individually within the group
                    }
                }
                
                override_url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/assignments/{assignment_id}/overrides"
                response = requests.post(override_url, headers=headers, json=data)
    
                if response.status_code in [200, 201]:
                    print(f"Assignment '{assignment_name}' (ID: {assignment_id}) successfully assigned to group '{group_name}' in practical '{practical_name}' with due date {submission_date.date()}.")
                else:
                    print(f"Failed to assign assignment '{assignment_name}' (ID: {assignment_id}) to group '{group_name}' in practical '{practical_name}'. Response: {response.text}")


    def remove_group_assignments(self, assignment_ids):
        """
        Removes all group assignments from the specified list of assignments in Canvas by deleting assignment overrides.
    
        Args:
            assignment_ids (list of int): List of assignment IDs from which to remove group assignments.
    
        Returns:
            None
        """
        # Define headers inside the function
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
        # Loop through each assignment ID
        for assignment_id in assignment_ids:
            # Fetch all overrides for the specified assignment
            url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/assignments/{assignment_id}/overrides"
            response = requests.get(url, headers=headers)
    
            if response.status_code != 200:
                print(f"Failed to fetch overrides for assignment {assignment_id}. Response: {response.text}")
                continue
    
            overrides = response.json()
    
            # Iterate through each override and delete if it is a group assignment
            for override in overrides:
                if override.get("group_id"):
                    override_id = override["id"]
                    delete_url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/assignments/{assignment_id}/overrides/{override_id}"
                    delete_response = requests.delete(delete_url, headers=headers)
    
                    if delete_response.status_code in [200, 204]:
                        print(f"Successfully removed group assignment override {override_id} from assignment {assignment_id}.")
                    else:
                        print(f"Failed to remove group assignment override {override_id} from assignment {assignment_id}. Response: {delete_response.text}")


