#-----------------------------------------------------------------------

# database.py

#-----------------------------------------------------------------------

import os
from sys import argv, stderr, exit
import psycopg2
from typing import Tuple, List
import requests, json

#-----------------------------------------------------------------------

class Database:

    # Initializes the database connection
    def __init__(self):
        self._connection = None

    #-----------------------------------------------------------------------

    # Connects to the Heroku PostgreSQL database
    def connect(self):
        DATABASE_URL = os.environ['DATABASE_URL']
        self._connection = psycopg2.connect(DATABASE_URL, sslmode='require')

    #-----------------------------------------------------------------------

    # Disconnects from the Heroku PostgreSQL database
    def disconnect(self):
        self._connection.close()

    #-----------------------------------------------------------------------

    # Checks if a user is in the database. If they are an existing user, 
    # update their profile information in the database. If they're a new
    # user, add their profile information to the database.
    def insert_user(self, id_token: str, first_name: str, last_name: str, email_address: str, notifications_enabled: bool, notification_frequency: int):
        try:
            if self.get_user_info(id_token) is not None:
                stmt_str = "UPDATE user_profiles SET FirstName = %s, LastName = %s, EmailAddress = %s, NotificationsEnabled = %s, NotificationFrequency = %s WHERE IDToken = %s"
                cursor = self._connection.cursor()
                cursor.execute(stmt_str, (first_name, last_name, email_address, notifications_enabled, notification_frequency, id_token))
                self._connection.commit()
                cursor.close()
            else:
                cursor = self._connection.cursor()

                stmt_str = "INSERT INTO user_profiles (IDToken, FirstName, LastName, EmailAddress, NotificationsEnabled, NotificationFrequency) VALUES (%s, %s, %s, %s, %s, %s)"

                cursor.execute(stmt_str, (id_token, first_name, last_name, email_address, notifications_enabled, notification_frequency))

                self._connection.commit()
                cursor.close()
        except Exception as e:
            print(e, file=stderr)

    #-----------------------------------------------------------------------

    # Returns the profile information of a user based on their unique id token.
    def get_user_info(self, id_token: str) -> tuple:
        try:
            cursor = self._connection.cursor()

            stmt_str = "SELECT * FROM user_profiles WHERE IDToken = %s"
            cursor.execute(stmt_str, (id_token,))

            row = cursor.fetchone()

            if row is None:
                user_info = None
            else:
                user_info: Tuple[str, str, str, str, bool, int] = (row[:])

            self._connection.commit()
            cursor.close()

            return user_info
        except Exception as e:
            print(e, file=stderr)
    
    #-----------------------------------------------------------------------

    # Returns the profile information for all of the users in the databse.
    def get_all_users(self) -> list:
        try:
            cursor = self._connection.cursor()

            stmt_str = "SELECT * FROM user_profiles"

            cursor.execute(stmt_str)

            row = cursor.fetchone()
            users = []
            while row is not None:
                users.append(row)
                row = cursor.fetchone()

            self._connection.commit()
            cursor.close()
            return users
        except Exception as e:
            print(e, file=stderr)

    #-----------------------------------------------------------------------

    # Inserts a site a user has favorited into the database (associated with
    # the user's id token).
    def insert_site_preference(self, id_token: str, site_token: str):
        try:
            cursor = self._connection.cursor()

            stmt_str = "INSERT INTO site_preferences (IDToken, SiteToken) VALUES (%s, %s)"

            cursor.execute(stmt_str, (id_token, site_token))

            self._connection.commit()
            cursor.close()
        except Exception as e:
            print(e, file=stderr)

    #-----------------------------------------------------------------------

    # Inserts a batch of sites a user has favorited into the database (associated with
    # the user's id token).
    def insert_site_preferences(self, id_token: str, site_tokens: list):
        try:
            cursor = self._connection.cursor()

            for x in range (0, len(site_tokens), 500):
                if(x > len(site_tokens)):
                     break
                sites_batch = site_tokens[x: min(x+500, len(site_tokens))]
                
                sites_str = ", ".join("(" + id_token + ", " + "'" + site + "'" + ")" for site in sites_batch)
                stmt_str = "INSERT INTO site_preferences (IDToken, SiteToken) VALUES %s" % (sites_str)

                cursor.execute(stmt_str)

            self._connection.commit()
            cursor.close()
        except Exception as e:
            print(e, file=stderr)

    #-----------------------------------------------------------------------

    # Removes a site a user has un-favorited from the database.
    def delete_site_preference(self, id_token: str, site_token: str):
        try:
            cursor = self._connection.cursor()

            stmt_str = "DELETE FROM site_preferences WHERE IDToken = %s AND SiteToken = %s"

            cursor.execute(stmt_str, (id_token, site_token))

            self._connection.commit()
            cursor.close()
        except Exception as e:
            print(e, file=stderr)

    #-----------------------------------------------------------------------

    # Removes all of the sites a user has previously favorited from the database.
    def delete_site_preferences(self, id_token: str, site_tokens: list):
        try:
            cursor = self._connection.cursor()

            sites_str = ", ".join("'" + site + "'" for site in site_tokens)

            stmt_str = "DELETE FROM site_preferences WHERE IDToken = '%s' AND SiteToken IN (%s)" % (id_token, sites_str)

            cursor.execute(stmt_str)

            self._connection.commit()
            cursor.close()
        except Exception as e:
            print(e, file=stderr)

    #-----------------------------------------------------------------------

    # Deletes the user's profile and saved-site information from the database.
    def delete_user(self, id_token: str):
        try:
            cursor = self._connection.cursor()

            stmt_str = "SELECT SiteToken FROM site_preferences WHERE IDToken = %s"
            cursor.execute(stmt_str, (id_token,))
            row = cursor.fetchone()
            while row is not None:
                self.delete_site_preference(id_token, str(row[0]))
                row = cursor.fetchone()

            stmt_str = "DELETE FROM user_profiles WHERE IDToken = %s"

            cursor.execute(stmt_str, (id_token,))

            self._connection.commit()
            cursor.close()
        except Exception as e:
            print(e, file=stderr)

    #-----------------------------------------------------------------------

    # Checks if a specific user has a specific site saved in the database.
    def has_site_preference (self, id_token: str, site_token: str):
        try:
            cursor = self._connection.cursor()

            stmt_str = "SELECT * FROM site_preferences WHERE IDToken = %s AND SiteToken = %s"
            cursor.execute(stmt_str, (id_token,site_token))

            row = cursor.fetchone()
            self._connection.commit()
            cursor.close()

            if row is not None:
                return True
            else:
                return False

        except Exception as e:
            print(e, file=stderr)

    #-----------------------------------------------------------------------

    # Returns a list of booleans associated with vaccination sites 
    # based on whether or not a user has saved a specific site in the database.
    def check_site_preferences (self, id_token: str, sites: list) -> list:
        try:
            cursor = self._connection.cursor()
            sites_str = ", ".join("'" + site["id"] + "'" for site in sites)

            stmt_str = "SELECT SiteToken FROM site_preferences WHERE IDToken = '%s' AND SiteToken IN (%s)" % (id_token, sites_str)
            cursor.execute(stmt_str)
            self._connection.commit()

            row = cursor.fetchone()

            favorited = dict()

            while row is not None:
                favorited[row[0]] = "True"
                row = cursor.fetchone()
            cursor.close()

            for site in sites:
                if(site["id"] in favorited):
                    site["favorited"] = True
                else:
                    site["favorited"] = False

            return sites

        except Exception as e:
            print(e, file=stderr)

    #-----------------------------------------------------------------------

    # Returns a list of all of the sites a single user has saved in our database.
    def get_site_preferences (self, id_token: str, allSites: list) -> list:
        try:
            cursor = self._connection.cursor()

            site_id_dict = dict()
            for site in allSites:
                site_id_dict[site['id']] = site

            stmt_str = "SELECT SiteToken FROM site_preferences WHERE IDToken = %s"
            cursor.execute(stmt_str, (id_token,))

            row = cursor.fetchone()
            site_info = []
            
            while row is not None:
                if site_id_dict.get(row[0]) is not None: site_info.append(site_id_dict[row[0]])
                row = cursor.fetchone()
            
            self._connection.commit()
            cursor.close()
            
            return site_info
        except Exception as e:
            print(e, file=stderr)