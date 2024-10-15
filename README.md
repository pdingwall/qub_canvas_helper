# qub_canvas_helper

This project is designed to automate the process of Canvas admin tasks.

## Features
Example Jupyter Notebooks are provided demonstrating the use of the following features.

### Assignments (assignment_manager)

- **`get_students_in_module()`**
  - Fetches all students enrolled in a specific Canvas course.
  - Outputs a DataFrame containing student `id`, `sis_user_id`, and names.

- **`check_student_enrollment(df_students)`**
  - Verifies if students from the Excel file are enrolled in the Canvas course.
  - Outputs discrepancies if any students are missing.

- **`get_assignments_in_module(self, published_status="all")`**
  - Fetches all assignments in a specific Canvas course.
  - Allows filtering by assignment status: `"all"` (default), `"published"`, or `"unpublished"`.
  - Returns a DataFrame containing assignment data, including assignment `id`, `name`, `due_at`, and `points_possible`.

- **`remove_student_assignments(self, assignment_ids)`**
  - Removes assignment overrides for a list of `assignment_ids` for all students in the course.
  - Confirms successful removal for each assignment and outputs any failures.

- **`assign_students_to_assignments(df_students, assignment_dict, check_enrollment=True)`**
  - Assigns Canvas assignments to students based on an Excel file supplied by the user.
  - Optionally checks for student enrollment before assigning.

- **`assign_assignment_to_student(student_id, student_name, assignment_id, due_date)`**
  - Creates an assignment override for a specific student.

### Calendars (calendar_manager)

- **`create_canvas_event(self, title, description, start_date, end_date, location)`**
  - Creates a new calendar event in Canvas with the specified `title`, `description`, `start_date`, `end_date`, and `location`.
  - Returns the event details if successful.

- **`upload_calendar(df)`**
  - Iterates through a DataFrame, created from an imported Excel file, to create Canvas calendar events.
  - Maps event details such as `title`, `description`, `location`, and `start/end time` to Canvas.

- **`fetch_event_by_id(self, event_id)`**
  - Fetches details for a specific calendar event using its `event_id`.
  - Returns event data including `title`, `start_at`, `end_at`, and `location`.

- **`fetch_course_calendar_events(start_date=None, end_date=None)`**
  - Fetches all calendar events from a Canvas course within a specified date range.
  - Returns a DataFrame with event details, including `title`, `start_at`, `end_at`, and `location`.

- **`remove_calendar_events(start_date=None, end_date=None)`**
  - Removes all calendar events from a Canvas course within the specified date range.
  - Confirms successful deletion by event title, time, and location.

## Requirements

To run this project, you need the following:

- **Python 3.x**
- 
- **Pandas**
- 
- **Requests**
- 
- **Access to Canvas API**
  - You'll need an API token from your institution's Canvas instance to interact with the Canvas API.

- **Excel File with Student Data**
  - Specific data formats must be followed for each manager.

## Canvas API token
Instructions on generating an API token from canvas can be found [here](https://community.canvaslms.com/t5/Canvas-Basics-Guide/How-do-I-manage-API-access-tokens-in-my-user-account/ta-p/615312) 

The script assumes the API token is an environment variable. To do this on Windows:

1. **Open the Start Menu**:
   - Click on the Start button (or press the Windows key).

2. **Search for "Environment Variables"**:
   - Type "Environment Variables" into the search bar.
   - Select **Edit the system environment variables** from the list of options.

3. **Open Environment Variables Window**:
   - In the **System Properties** window that opens, click on the **Environment Variables** button near the bottom.

4. **Create a New User Variable**:
   - In the **Environment Variables** window, under the **User variables** section, click the **New** button.

5. **Add the Variable Name and Value**:
   - In the **Variable name** field, type: `CANVAS_API_TOKEN`.
   - In the **Variable value** field, paste your Canvas API token (make sure there are no extra spaces before or after).

6. **Save the Variable**:
   - Click **OK** to save the new environment variable.
   - Click **OK** again in the **Environment Variables** window and close the system properties window.

7. **Verify the Variable**:
   - Open a new **Command Prompt** window and type the following command to check if the variable was set correctly:
     ```bash
     echo %CANVAS_API_TOKEN%
     ```
   - If the variable was set correctly, you should see your Canvas API token printed to the screen.