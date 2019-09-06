#!/usr/bin/env python
# -- coding: utf-8 --
# license removed for brevity
 
import rospy
import time
from datetime import datetime
import std_msgs.msg
from math import sqrt
import numpy as np
from random import randint
from random import uniform
from indoor_localization.msg import AnchorScan
import collections

def init_robot():
    """ Initialize the start location of robot randomly """

    initial_Tx = float(100.0)                   # float(rospy.get_param("/simulator/initial_Tx")) 
    initial_Ty = float(100.0)                   # float(rospy.get_param("/simulator/initial_Ty")) 
    initial_Tz = float(1.10)                   # float(rospy.get_param("/simulator/initial_Tz"))
    initial_angle = float(2 * np.pi* 0.2)       # float(2 * np.pi * np.random.rand())

    initial_pos = list([initial_Tx, initial_Ty, initial_Tz, initial_angle])

    return initial_pos


def init_velocity():

    velocity = float(1.0)       # (m/s)
    return velocity


def init_rate():
    """ This rate indicates the recorded positions' intervals. """

    rate = float(0.1)       # (Hz)
    return rate


def init_anchors():

    anchor_info = dict()
    anchor_id = list()

    for x in range(20, 160, 20):
        for y in range(20, 160, 20):
            
            coord_list = list()

            z = float(10.0)     # 4 + 3 * uniform(0, 1)

            coord_list.append(float(x))
            coord_list.append(float(y))
            coord_list.append(float(z))

            anchor_id = randint(0, 100)
            anchor_info[anchor_id] = coord_list

    return anchor_info


#----------------------------
def signal_received_anchors(anchor_info):
    """ Bir bolgedeki 49 tane ankorun 10 tanesinden sinyal alindiigini varsayalim. """

    anchor_info_ids = list(anchor_info.keys())
    anchor_info_coords = list(anchor_info.values())        # all anchors in system

    signal_received_anchor_info = dict()

    sig = 10

    for cnt in range(sig):

        sig_rec_coord_list = list()
        sig_rec_coord_list.extend(anchor_info_coords[cnt])

        signal_received_anchor_info[anchor_info_ids[cnt]] = sig_rec_coord_list

    return signal_received_anchor_info


def min_ind_of_anch(anchor_info):
    """ Minimum ID'nin kaçıncı indexte olduğunu bulur. """
    
    anch_id = list(anchor_info.keys())
    min_id_ind = anch_id.index(min(anch_id))

    return min_id_ind


def robot_harekete_basla(velocity, rate, initial_pos):
    """ Robot starts to move with specified velocity.
    When the robot hits to the edges, next move's angle is calculated.
    Robot's move ends when total drop number is 5.
    """

    move = True         # if false -> No Movement
    total_drop = 5      # number of drop to the edges
    drop_count = 0      # drop counter
    pos_count = 0       # position counter
    
    first_Tx = initial_pos[0]
    first_Ty = initial_pos[1]
    first_Tz = initial_pos[2]
    angle = initial_pos[3]

    coords_x = list()
    coords_y = list()
    coords_z = list()

    coords_x.append(first_Tx)
    coords_y.append(first_Ty)
    coords_z.append(first_Tz)

    while move:

        new_Tx = first_Tx + np.cos(angle)*rate   # velocity * np.cos(angle)
        new_Ty = first_Ty + np.sin(angle)*rate   # velocity * np.sin(angle)
        new_Tz = first_Tz
        pos_count = pos_count + 1

        coords_x.append(new_Tx)
        coords_y.append(new_Ty)
        coords_z.append(new_Tz)

        if new_Tx > 160:
            #print('\n Tag sağ sınıra çarptı!')
            angle = 2*np.pi - angle + np.pi
            drop_count = drop_count + 1


        elif new_Tx < 0:
            #print('\n Tag sol sınıra çarptı!')
            angle = 2*np.pi - angle + np.pi
            drop_count = drop_count + 1


        elif new_Ty > 160:
            #print('\n Tag üst sınıra çarptı!')
            angle = 2*np.pi - angle
            drop_count = drop_count + 1


        elif new_Ty < 0:
            #print('\n Tag alt sınıra çarptı!')
            angle = 2*np.pi - angle
            drop_count = drop_count + 1


        if drop_count > total_drop:
            move = False

        first_Tx = new_Tx
        first_Ty = new_Ty
        first_Tz = new_Tz

    only_movable_positions= list()

    for row in range(pos_count):
        only_movable_positions.append([coords_x[row], coords_y[row], coords_z[row]])

    return only_movable_positions


def calc_stop_pos(pos, count):

    stop_list = list()
    
    for i in range(count):
        stop_list.append(pos)
    
    return stop_list


def add_stop_pos(only_movable_positions):
    """ Olusturulan harekete durdugu pozisyonlar eklendi. """

    print(len(only_movable_positions))

    stop1 = calc_stop_pos(only_movable_positions[150], 60)
    stop2 = calc_stop_pos(only_movable_positions[150+250], 60)
    stop3 = calc_stop_pos(only_movable_positions[150+250+200], 20)

    positions_with_stop = list()
    positions_with_stop.extend(only_movable_positions[0:150])
    positions_with_stop.extend(stop1)
    positions_with_stop.extend(only_movable_positions[150:(150+250)])
    positions_with_stop.extend(stop2)
    positions_with_stop.extend(only_movable_positions[(150+250):(150+250+200)])
    positions_with_stop.extend(stop3)
    positions_with_stop.extend(only_movable_positions[(150+250+200):])

    #new_pos_array = np.array(positions_with_stop)
    #np.savetxt("new_pos_array.txt", new_pos_array)

    return positions_with_stop


def generate_radius(anchor_info, finalised_positions):
    """ Sinyal alinabilen ankorların her birinin her bir konuma olan uzakligi """

    anch_id = list(anchor_info.keys())
    anch_coord = list(anchor_info.values())

    all_radius_list = list()

    for row in range(len(finalised_positions)):
        one_pos_radius_dict = dict()
        for cnt_anch in range(len(anch_id)):
            radius = sqrt(pow((finalised_positions[row][0]-anch_coord[cnt_anch][0]), 2) 
                     + pow((finalised_positions[row][1]-anch_coord[cnt_anch][1]), 2) 
                     + pow((finalised_positions[row][2]-anch_coord[cnt_anch][2]), 2))
            one_pos_radius_dict[anch_id[cnt_anch]] = radius
        all_radius_list.append(one_pos_radius_dict)

    return all_radius_list


def select_reference_radius(anchor_info, finalised_positions, all_radius_list, min_id_ind):

    reference_radius = list()       # her pozisyon icin bir ref
    anch_id = list(anchor_info.keys())

    for row in range(len(finalised_positions)):
        sample = all_radius_list[row]
        reference_radius.append(sample[anch_id[min_id_ind]])

    return reference_radius


def generate_pure_ddoa(sig_anchor_info, finalised_positions, all_radius_list, reference_radius, min_id_ind):

    pure_ddoa_all_pos = list()
    anch_id = list(sig_anchor_info.keys())

    for cnt_pos in range(len(finalised_positions)):
        pure_ddoa_one_pos = list()
        sample = all_radius_list[cnt_pos]

        for cnt_anch in range(len(anch_id)):
            if cnt_anch != min_id_ind:
                ddoa_one_pos = sample[anch_id[cnt_anch]] - reference_radius[cnt_pos]
                pure_ddoa_one_pos.append(ddoa_one_pos)

            else:
                pass
        
        pure_ddoa_all_pos.append(pure_ddoa_one_pos)

    return pure_ddoa_all_pos



def publisher():

    rospy.init_node("simulator", anonymous=True)
    pub = rospy.Publisher('IPS', AnchorScan, queue_size=2)
    rate = rospy.Rate(10)
    
    initial_tag_pos = init_robot()
    velocity = init_velocity()
    pos_rate = init_rate()
    all_anchor_info = init_anchors()
    #----------------------------

    only_movable_positions = robot_harekete_basla(velocity, pos_rate, initial_tag_pos)
    finalised_positions = add_stop_pos(only_movable_positions)
    
    sig_anchor_info = signal_received_anchors(all_anchor_info)
    sig_anchor_id = list(sig_anchor_info.keys()) 
    sig_anchor_coordinates = sig_anchor_info.values()         # coordinates

    min_id_ind = min_ind_of_anch(sig_anchor_info)

    radius_list = generate_radius(sig_anchor_info, finalised_positions)
    reference_radius = select_reference_radius(sig_anchor_info, finalised_positions, radius_list, min_id_ind)
    pure_ddoa_list = generate_pure_ddoa(sig_anchor_info, finalised_positions, radius_list, reference_radius, min_id_ind)

    tmp_anchor_coords_x = list()
    tmp_anchor_coords_y = list()
    tmp_anchor_coords_z = list()

    for cnt in range(len(sig_anchor_id)):
        tmp_anchor_coords_x.append(sig_anchor_info[sig_anchor_id[cnt]][0])
        tmp_anchor_coords_y.append(sig_anchor_info[sig_anchor_id[cnt]][1])
        tmp_anchor_coords_z.append(sig_anchor_info[sig_anchor_id[cnt]][2])

    cnt = 0
    while not rospy.is_shutdown():
        msg = AnchorScan()
        msg.header.stamp = rospy.Time.now()
        msg.AnchorID = sig_anchor_id    # publishes the signal received anchors' IDs
        msg.x = tmp_anchor_coords_x     # publishes the signal received anchors' positions
        msg.y = tmp_anchor_coords_y
        msg.z = tmp_anchor_coords_z
        msg.tdoa_of_anchors = pure_ddoa_list[cnt-1][:]

        print("\tSIMULATION POS: " + str(finalised_positions[cnt]))

        if cnt < len(finalised_positions) - 1:
            cnt = cnt + 1
        else:     
            print("\n\t\t END OF DATA \t\t\n")       
            break       # pub.unregister()  !!!***!!!***!!!***!!!***!!!***!!!***!!!
        pub.publish(msg)
        rate.sleep()


if __name__ == '__main__':
    try:
        publisher()
    except rospy.ROSInterruptException:
        pass

