"""
rm_define.media_custom_audio_0: Enemy Spotted
rm_define.media_custom_audio_1: HEHEHEHAW
rm_define.media_custom_audio_2: Dropoff 1
rm_define.media_custom_audio_3: Dropoff 2
rm_define.media_custom_audio_4: Pickup
rm_define.media_custom_audio_5: Starting
"""


# ID for Vision Markers
left_id = 12 # 2
right_id = 11 # 1
junct_1 = 47 # ?
junct_2 = 8 # Heart
bag_1 = 14 # 4
bag_2 = 15 # 5
bag_3 = 16 # 6
bag_4 = 17 # 7
drop_id = 13 # 3
bags_deposited = 0 # Element of {0, 1, 2, 3, 4}
bag_lst = [bag_1, bag_2, bag_3, bag_4]

# (JUNCTION 1, JUNCTION 2)
# False - Left
# True - Right
bag_at_junction = {
    bag_1: (False, False),
    bag_2: (False, True),
    bag_3: (True, False),
    bag_4: (True, True)
}


def pickup():
    # Move arm to top of baggage
    robotic_arm_ctrl.moveto(182, 109, wait_for_complete=False)
    robotic_arm_ctrl.moveto(182, -10, wait_for_complete=True)
    time.sleep(0.5)

    gripper_ctrl.close()

    # Lift up baggage
    time.sleep(1.5)
    robotic_arm_ctrl.moveto(74, 57, wait_for_complete=True)


def putdown():
    # Move baggage down
    robotic_arm_ctrl.moveto(182, 109, wait_for_complete=False)
    robotic_arm_ctrl.moveto(182, -10, wait_for_complete=True)
    time.sleep(0.5)

    gripper_ctrl.open()
    time.sleep(1.5)

    # Move back so baggage won't take knocked over
    chassis_ctrl.move_with_time(-180, 0.5)

    # Lift arm up
    robotic_arm_ctrl.moveto(182, 0, wait_for_complete=False)
    robotic_arm_ctrl.moveto(86, 0, wait_for_complete=True)


def turn_where(bag_id):
    """
    Returns where to turn the robot once a vision marker is seen.

    Args:
        -> bag_id: ID of the current baggage (14, 15, 16, 17), 0 if no baggage

    Return Vals:
        -> 0    : Don't turn
        -> 90   : Turn Right
        -> -90  : Turn Left
        -> 180  : Drop baggage
        -> 14   : Baggage 4 found
        -> 15   : Baggage 5 found
        -> 16   : Baggage 6 found
        -> 17   : Baggage 7 found
    """

    # Get vision marker information
    markers = vision_ctrl.get_marker_detection_info()

    # No marker detected
    if markers[0] == 0:
        return 0

    marker_id = markers[1]

    # Junction 1
    if marker_id == junct_1:
        # If robot has a baggage
        if bag_id != 0:
            # Get the turn from dictionary
            if bag_at_junction[bag_id][0]:
                return 90
            return -90

    # Junction 2
    if marker_id == junct_2:
        # If robot has a baggage
        if bag_id != 0:
            # Get the turn from dictionary
            if bag_at_junction[bag_id][1]:
                return 90
            return -90

    # Left Turn
    if marker_id == left_id:
        return -90

    # Right Turn
    if marker_id == right_id:
        return 90

    # Baggage Dropoff
    if marker_id == drop_id:
        return 180

    # Baggage Detected
    if marker_id in bag_lst:
        return marker_id


def centeris_paribus():
    """
    Centers and positions robot in front of required vision marker

    Args:
        -> marker_id: ID of the marker detected
    """
    # Slow down before centering
    chassis_ctrl.set_trans_speed(0.5)

    # Get necessary information about vision markers
    #   i.e. the ID and the x-coordinate for centering
    markers = vision_ctrl.get_marker_detection_info()
    if len(markers) == 1: # No marker
        return
    marker_id = markers[1]
    x_coord = markers[2]

    # Center the marker horizontally
    if x_coord > 0.5:
        # Marker right of center: Move right
        dist = x_coord - 0.5
        chassis_ctrl.move_with_distance(90, dist)
    else:
        # Marker left of center: Move left
        dist = 0.5 - x_coord
        chassis_ctrl.move_with_distance(-90, dist)

    # Move forward to vision marker
    chassis_ctrl.move(0)

    # Non-Baggage
    if not marker_id in bag_lst:
        dist_to_marker = ir_distance_sensor_ctrl.get_distance_info(1)
        while dist_to_marker > 20:
            time.sleep(0.1)
            dist_to_marker = ir_distance_sensor_ctrl.get_distance_info(1)
    # Baggage
    else:
        dist_to_bag = ir_distance_sensor_ctrl.get_distance_info(1)
        while dist_to_bag > 15:
            time.sleep(0.1)
            dist_to_bag = ir_distance_sensor_ctrl.get_distance_info(1)
    chassis_ctrl.stop()

    # Speed up after centering
    chassis_ctrl.set_trans_speed(3.5)


def start():
    bag_id = 0

    # Initialize arm
    robotic_arm_ctrl.moveto(200, -70, wait_for_complete=False)
    gripper_ctrl.open()

    # Initialize Vision Marker detection
    vision_ctrl.enable_detection(rm_define.vision_detection_marker)
    vision_ctrl.set_marker_detection_distance(3)
    
    # Initialize IR Sensor detection
    ir_distance_sensor_ctrl.enable_measure(2)

    # Initialize movement speed
    chassis_ctrl.set_trans_speed(3.5) # m/s
    chassis_ctrl.set_rotate_speed(180) # Degree/s

    media_ctrl.play_sound(rm_define.media_custom_audio_5, wait_for_complete_flag=False) # Starting Audio

    while True:
        chassis_ctrl.move(0)
        time.sleep(0.2)

        turn_result = turn_where(bag_id)
        if turn_result in bag_lst:
            # Update which bag is currently with the bot
            bag_id = turn_result
        
        # Right turn
        if turn_result == 90:
            chassis_ctrl.stop()
            centeris_paribus()
            chassis_ctrl.rotate_with_degree(rm_define.clockwise, 90)
        # Left turn
        elif turn_result == -90:
            chassis_ctrl.stop()
            centeris_paribus()
            chassis_ctrl.rotate_with_degree(rm_define.anticlockwise, 90)
        # Pickup Baggage
        elif turn_result in bag_lst:
            if bags_deposited >= 2:
                media_ctrl.play_sound(rm_define.media_custom_audio_1, wait_for_complete_flag=False) # "HEHEHEHAW"
            else:
                media_ctrl.play_sound(rm_define.media_custom_audio_0, wait_for_complete_flag=False) # "Enemy Spotted"
            chassis_ctrl.stop()
            centeris_paribus()
            pickup()
            media_ctrl.play_sound(rm_define.media_custom_audio_4, wait_for_complete_flag=False) # Pickup Audio
        # Dropoff Baggage
        elif turn_result == 180:
            chassis_ctrl.stop()
            centeris_paribus()
            putdown()
            bag_id = 0 # Bot no longer has a bag
            bags_deposited += 1
            if bags_deposited % 2 == 0:
                media_ctrl.play_sound(rm_define.media_custom_audio_2, wait_for_complete_flag=False) # Dropoff 1
            else:
                media_ctrl.play_sound(rm_define.media_custom_audio_3, wait_for_complete_flag=False) # Dropoff 2
            chassis_ctrl.rotate_with_degree(rm_define.clockwise, 180)
