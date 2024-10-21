import pandas as pd
import requests
from datetime import datetime, timedelta
from ics import Calendar
from ics import Event

class CanvasCalendarManager:
    """
    A class to handle the creation of calendar events in a Canvas course.

    Attributes:
        canvas_domain (str): The Canvas domain URL (e.g., "https://qub.instructure.com").
        access_token (str): The access token for the Canvas API.
        course_id (int): The ID of the Canvas course.
    """
    
    def __init__(self, canvas_domain, access_token, course_id):
        """
        Initializes the Calendar class with the Canvas domain, access token, and course ID.

        Args:
            canvas_domain (str): The Canvas domain URL (e.g., "https://qub.instructure.com").
            access_token (str): The access token for Canvas API.
            course_id (int): The ID of the Canvas course.
        """
        self.canvas_domain = canvas_domain
        self.access_token = access_token
        self.course_id = course_id


    def create_canvas_event(self, title, description, start_date, end_date, location):
        """
        Creates a calendar event in the specified Canvas course.

        Args:
            title (str): The title of the event.
            description (str): A description of the event.
            start_date (datetime): The start date and time of the event as a datetime object.
            end_date (datetime): The end date and time of the event as a datetime object.
            location (str): The location of the event.
        
        Returns:
            dict: The JSON response from the Canvas API with details of the created event.
        
        Raises:
            Exception: If the API request fails.
        """
        url = f"{self.canvas_domain}/api/v1/calendar_events"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "calendar_event": {
                "context_code": f"course_{self.course_id}",
                "title": title,
                "description": description,
                "start_at": start_date.isoformat(),
                "end_at": end_date.isoformat(),
                "location_name": location
            }
        }
        
        # Send a POST request to create the override
        response = requests.post(url, json=payload, headers=headers)
    
        # Check the response status code
        if 200 <= response.status_code < 300:  # Treat as success if status code is between 200-299
            #print(f"Event created: {title}")
            return response.json()
        else:
            #print(f"Failed to create event {title}. Response: {response.json()}")
            return response.json()

    def upload_calendar(self, df):
        """
        Iterates over each row in the DataFrame and creates Canvas events for each row.
        Before creating an event, it checks if there is already an event scheduled in the same time slot.
    
        Args:
            df (pd.DataFrame): A DataFrame containing event details like 'Topic', 'Staff', 'Room',
                                            'Start Time', 'End Time', and 'Date'.
    
        Returns:
            None: Prints responses after creating each event on Canvas.
        """
        for index, row in df.iterrows():
            # Construct the title, description, and location
            title = f"{row['Topic'] if pd.notna(row['Topic']) else 'No Topic'}"
            description = f"Supervised by {row['Staff']}" if pd.notna(row['Staff']) else "No additional notes"
            location = row['Room'] if pd.notna(row['Room']) else "No specified location"
            
            # Combine date with start and end times
            start_time = row['Start Time']
            end_time = row['End Time']
            date = pd.to_datetime(row['Date']).date()
    
            start_datetime = pd.Timestamp.combine(date, start_time)
            end_datetime = pd.Timestamp.combine(date, end_time)
    
            # Make sure both start and end datetimes are timezone-naive to match the event times from Canvas
            start_datetime = pd.Timestamp(start_datetime).tz_localize(None)
            end_datetime = pd.Timestamp(end_datetime).tz_localize(None)
    
            # Check for any existing events in the same time slot before creating a new event
            existing_events = self.fetch_course_calendar_events(start_date=start_datetime.strftime('%Y-%m-%d'),
                                                                end_date=end_datetime.strftime('%Y-%m-%d'))
    
            # Check if there are any existing events and handle conflicts
            if not existing_events.empty:
                # Convert existing event times to timezone-naive for proper comparison
                existing_events['start_at'] = pd.to_datetime(existing_events['start_at']).dt.tz_localize(None)
                existing_events['end_at'] = pd.to_datetime(existing_events['end_at']).dt.tz_localize(None)
    
                # Filter events that overlap with the new event's start and end times
                conflicting_events = existing_events[
                    (existing_events['start_at'] < end_datetime) &
                    (existing_events['end_at'] > start_datetime)
                ]
    
                if not conflicting_events.empty:
                    # If there's a conflict, skip creating this event and print conflict details
                    conflict_time = start_datetime.strftime("%Y-%m-%d at %H:%M")
                    print(f"Conflict detected for {title} on {conflict_time}. Skipping creation.")
                    continue
    
            # Create the event on Canvas
            try:
                response = self.create_canvas_event(
                    title=title,
                    description=description,
                    start_date=start_datetime,
                    end_date=end_datetime,
                    location=location
                )
                
                # Filter and print only specific information from the response
                event_id = response.get('id')
                event_title = response.get('title')
                start_formatted = pd.to_datetime(response.get('start_at')).strftime("%H:%M on %Y-%m-%d")
                end_formatted = pd.to_datetime(response.get('end_at')).strftime("%H:%M on %Y-%m-%d")
                location_name = response.get('location_name')
    
                print(f"Event created for {event_title}: ID {event_id}, Start: {start_formatted}, End: {end_formatted}, Location: {location_name}")
            
            except Exception as e:
                print(f"Failed to create event for {title}: {e}")

    def fetch_event_by_id(self, event_id):
        """
        Fetches details of a specific calendar event by its ID from Canvas and returns the data as a DataFrame.
    
        Args:
            event_id (int): The ID of the calendar event to fetch.
    
        Returns:
            pd.DataFrame: A DataFrame containing the details of the event.
    
        Raises:
            Exception: If the API request fails.
        """
        url = f"{self.canvas_domain}/api/v1/calendar_events/{event_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
        # Send the GET request to fetch the event details
        response = requests.get(url, headers=headers)
    
        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"Failed to fetch event: {response.status_code}, {response.text}")
    
        # Parse the response JSON
        event_data = response.json()
    
        # Check if it's a dictionary (single event) or list and convert to a DataFrame
        if isinstance(event_data, dict):
            df_event = pd.DataFrame([event_data])  # Convert the dict to a DataFrame with one row
        else:
            df_event = pd.DataFrame(event_data)  # Convert a list of events to a DataFrame
    
        return df_event
        
    def fetch_course_calendar_events(self, start_date=None, end_date=None):
        """
        Fetches all calendar events for the specified Canvas course (module) within a date range, handling pagination if necessary.
    
        Args:
            start_date (str): The start date in the format "YYYY-MM-DD" (optional).
            end_date (str): The end date in the format "YYYY-MM-DD" (optional).
    
        Returns:
            pd.DataFrame: A DataFrame containing all the calendar events for the course within the specified date range.
    
        Raises:
            Exception: If the API request fails.
        """
        url = f"{self.canvas_domain}/api/v1/calendar_events"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
        # Add date range to the params if provided
        params = {
            "context_codes[]": f"course_{self.course_id}",
            "per_page": 100  # Adjust if needed
        }
    
        if start_date:
            params["start_date"] = start_date
    
        if end_date:
            params["end_date"] = end_date
    
        events = []
        while url:
            response = requests.get(url, headers=headers, params=params)
    
            if response.status_code != 200:
                raise Exception(f"Failed to fetch events: {response.status_code}, {response.text}")
    
            events.extend(response.json())
    
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
    
        # Convert the list of events to a DataFrame
        df_events = pd.DataFrame(events)
        return df_events
    
    def remove_calendar_events(self, start_date=None, end_date=None):
        """
        Removes calendar events for the specified Canvas course (module) within a date range, handling pagination if necessary.
        The date and time of each removed event will be printed in the format "on MM/DD/YYYY at HH:MM".
    
        Args:
            start_date (str): The start date in the format "YYYY-MM-DD" (optional).
            end_date (str): The end date in the format "YYYY-MM-DD" (optional).
    
        Raises:
            Exception: If the API request fails.
        """
        url = f"{self.canvas_domain}/api/v1/calendar_events"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
        # Add date range to the params if provided
        params = {
            "context_codes[]": f"course_{self.course_id}",
            "per_page": 100  # Adjust as needed (Canvas API usually paginates by 10-100 items per page)
        }
    
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
    
        # Fetch all events with pagination
        events = []
        while url:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch events: {response.status_code}, {response.text}")
            
            events.extend(response.json())
            
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
    
        # Step 2: Iterate over the events and delete each one
        for event in events:
            event_id = event['id']
            delete_url = f"{self.canvas_domain}/api/v1/calendar_events/{event_id}"
    
            # Get the event start time and format it
            event_time = pd.to_datetime(event['start_at'])
            formatted_time = event_time.strftime("on %m/%d/%Y at %H:%M")
    
            # Send delete request
            delete_response = requests.delete(delete_url, headers=headers)
    
            if delete_response.status_code == 200:
                print(f"Successfully removed event {event['title']} (ID: {event_id}) {formatted_time}")
            else:
                print(f"Failed to remove event {event['title']} (ID: {event_id}) {formatted_time}. Response: {delete_response.json()}")

    
    ########################################### THE FUNCTIONS BELOW ARE FOR CREATING OUTLOOK CALENDARS ################################################


class CanvasOutlookCalendarManager:
    """
    A class to handle the creation of ICS calendar files from a DataFrame for Outlook.
    """
    
    def combine_date_time(self, date, time):
        """
        Combines a date and time into a single datetime object.

        Args:
            date (datetime.date): The date value.
            time (datetime.time or str): The time value, which can be either a datetime.time object or a string
                                         in '%H:%M:%S' format.

        Returns:
            datetime.datetime: A combined datetime object with the specified date and time.
        """
        # Check if time is a string, then parse it
        if isinstance(time, str):
            time = datetime.strptime(time, '%H:%M:%S').time()
        return datetime.combine(date, time)
    
    def create_outlook_calendar(self, df, calendar_name):
        """
        Creates an ICS calendar from a DataFrame and saves it to a file.

        Args:
            df (pd.DataFrame): A DataFrame where each row contains the following columns:
                               - 'EventName': The name/title of the event.
                               - 'Date': The date of the event.
                               - 'Start Time': The start time of the event.
                               - 'End Time': The end time of the event.
                               - 'Room': The location of the event.
            calendar_name (str): The full name (including path) of the .ics calendar file.
        
        Returns:
            None: Saves the ICS calendar to the specified file.
        """
        # Initialize the calendar
        calendar = Calendar()

        # Loop through each row and create an event
        for index, row in df.iterrows():
            event = Event()
            
            # Use .get() to avoid KeyErrors if columns are missing
            event.name = str(row.get('EventName', 'Unnamed Event'))
            event.begin = self.combine_date_time(row['Date'], row['Start Time'])
            event.end = self.combine_date_time(row['Date'], row['End Time'])
            event.location = str(row.get('Room', 'No Location'))

            # Custom category for the event
            event.categories = ["Lectures"]
            
            calendar.events.add(event)
        
        # Save the calendar to the specified file
        with open(f"{calendar_name}.ics", 'w') as f:
            f.writelines(calendar)
        
        print(f"Calendar {calendar_name}.ics created")

    
    ########################################### THE FUNCTIONS BELOW DO NOT (YET) WORK ################################################


    def fetch_course_timetable(self, start_date=None, end_date=None):
        """
        Fetches the course timetable, including assignments, quizzes, and other calendar events for the specified course within a date range.
    
        Args:
            start_date (str): The start date in the format "YYYY-MM-DD" (optional).
            end_date (str): The end date in the format "YYYY-MM-DD" (optional).
    
        Returns:
            pd.DataFrame: A DataFrame containing the details of the course's timetable (calendar events).
    
        Raises:
            Exception: If the API request fails.
        """
        # API endpoint to get the timetable (calendar events) for the course
        url = f"{self.canvas_domain}/api/v1/courses/{self.course_id}/calendar_events/timetable"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
        # Add date range to the params if provided
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
    
        # Send GET request to the timetable endpoint
        response = requests.get(url, headers=headers, params=params)
    
        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"Failed to fetch course timetable: {response.status_code}, {response.text}")
    
        # Parse the response JSON
        timetable = response.json()
    
        # Convert the timetable list to a DataFrame
        if timetable:
            df_timetable = pd.DataFrame(timetable)
        else:
            print("No events found for this course.")
            return pd.DataFrame()  # Return an empty DataFrame if no events are found
    
        # Return the DataFrame with the course timetable (events)
        return df_timetable

   


