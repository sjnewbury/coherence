"""
dimming_client

Sends supported commands to ???

Implements Dimming:1 UPnP protocol

This is called only from dimmable_light_client.py.
"""

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php
# Copyright 2008, Frank Scholz <coherence@beebits.net>

class DimmingClient:
    """

    Only instantiated from dimmable_light_client.py
    There is one instance for each service in a device.
    """

    def __init__(self, service):
        self.service = service
        self.namespace = service.get_type()
        self.url = service.get_control_url()
        self.service.subscribe()
        self.service.client = self

    def remove(self):
        self.service.remove()
        self.service = None
        self.namespace = None
        self.url = None
        del self

    def subscribe_for_variable(self, var_name, callback, signal = False):
        self.service.subscribe_for_variable(var_name, instance = 0, callback = callback, signal = signal)

    def set_load_level_target(self, new_load_level_target = 0):
        action = self.service.get_action('SetLoadLevelTarget')
        return action.call(NewLoadLevelTarget = new_load_level_target)

    def get_load_level_target(self):
        """
        @return: a deferred that gets the light's load level target.
        """
        action = self.service.get_action('GetLoadLevelTarget')
        return action.call()

    def get_load_level_status(self):
        action = self.service.get_action('GetLoadLevelStatus')
        return action.call()

    '''DBK  - I added the rest of these from the UPnP docs.
    '''

    def set_on_effect_level(self, new_on_effect_level = 0):
        action = self.service.get_action('SetOnEffectLevel')
        return action.call(NewOnEffectLevel = new_on_effect_level)

    def set_on_effect(self, new_on_effect = 'yes'):
        action = self.service.get_action('SetOnEffect')
        return action.call(NewOnEffect = new_on_effect)

    def get_on_effect_parameters(self):
        pass

    def step_up(self):
        pass

    def step_down(self):
        pass

    def start_ramp_up(self):
        pass

    def start_ramp_dawn(self):
        pass

    def stop_ramp(self):
        pass

    def start_ramp_to_level(self):
        pass

    def set_step_delta(self):
        pass

    def get_step_delta(self):
        pass

    def set_ramp_rate(self, new_ramp_rate = 25):
        pass

    def get_ramp_rate(self):
        pass

    def pause_ramp(self):
        pass

    def resume_ramp(self):
        pass

    def get_ramp_paused(self):
        pass

    def get_ramp_time(self):
        pass

    def get_is_ramping(self):
        pass

### END
