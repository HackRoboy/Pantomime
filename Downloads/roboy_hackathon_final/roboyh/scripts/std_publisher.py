#!/usr/bin/env python
# license removed for brevity
import rospy
#import rospy.rostime

#from rospy.rostime import Duration
from std_msgs.msg import Float64MultiArray, MultiArrayLayout, MultiArrayDimension

import base64
import os
import random

import pyttsx
import time

from difflib import SequenceMatcher as similarity

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials

import numpy

DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')


def get_speech_service():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)

    return discovery.build(
        'speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)


def get_transcription(speech_file):
    with open(speech_file, 'rb') as speech:
        speech_content = base64.b64encode(speech.read())

    service = get_speech_service()
    service_request = service.speech().syncrecognize(
        body={
            'config': {
                'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                'sampleRate': 16000,  # 16 khz
                'languageCode': 'en-US',  # a BCP-47 language tag
            },
            'audio': {
                'content': speech_content.decode('UTF-8')
            }
        })
    response = service_request.execute()
    if response:
        sentence = response['results'][0]['alternatives'][0]['transcript']
        say_and_print('I heard: ' + sentence)
        return sentence
    else:
        return None


def guess_game(robot_move):
    print '*** Moving Robot performing {}... ***'.format(robot_move)
    move_along_trajectory(robot_move)

    while True:
        say_and_print('Press enter and say your guess')
        raw_input('')
        os.system('arecord -q -t wav -d 2 -f S16_LE -r 16000 filename.wav')
        answer = get_transcription('filename.wav')

	is_Similar = False
	if answer:
		is_Similar = similarity(None, answer.lower(), robot_move).ratio()*100 > 75

        if not answer:
            say_and_print('I could not understand, please retry')
        elif answer.lower() == robot_move or is_Similar:
            say_and_print('Good job! Correct answer!')
            break
	else:
            moves = ["kick", "nod", "shake"]
            options = [["kick", "kik"], ["nod", "note", "not", "notes"], ["shake"]]
            index = moves.index(robot_move)
            if (answer.lower() in options[index]):
              say_and_print('Good job! Correct answer!')
	      break
            else:
              say_and_print('Nope, wrong answer! Try again...')
            #break
        #else:
            #say_and_print('Nope, wrong answer! Try again...')

        os.system('rm filename.wav')


def say_and_print(sentence):
    print sentence
    engine = pyttsx.init()
    engine.setProperty('voice', 'english')
    engine.say(sentence)
    engine.runAndWait()


def move_along_trajectory(move):
    array_trajectory = load_movement_trajectory(move)

    for iterI in range(len(array_trajectory[:,0])):
        print iterI
        publish_data(array_trajectory[iterI,:])
        time.sleep(0.2)

def load_movement_trajectory(movement):
    file_name = movement + '.csv'
    print(file_name)
    array_data = numpy.genfromtxt(file_name, delimiter=',')
    
    return array_data

def publish_data(JointStates):
    try:
        sendTrajectory(JointStates)
    except rospy.ROSInterruptException:
	pass
    return 0

def sendNodTrajectory():
    rospy.init_node('chatter', anonymous=True)

    pub = rospy.Publisher('/rrbot/joint_position_controller/command', Float64MultiArray, queue_size=1000)
    rate = rospy.Rate(0.1) # 10hz
    cntIter = 0
    while not rospy.is_shutdown() and cntIter < 2:
    #only send a single joint movement, the rest is set to 0
       hello_str = "Publish a trajectory %s" % rospy.get_time()
       rospy.loginfo(hello_str)
    #prepare a trajectory

       jointNr = 43
       mat = Float64MultiArray()
       mat.data = [0.0]*jointNr
       mat.data[41] = 30 #joint nr 47 (5 joints are missing from the list)
       cntIter += 1
       print(mat.data)

       pub.publish(mat)
#    spinOnce()
       #print(mat)
       rate.sleep()



def sendTrajectory(JointStates):
    rospy.init_node('chatter', anonymous=True)

    pub = rospy.Publisher('/rrbot/joint_position_controller/command', Float64MultiArray, queue_size=1000)
    rate = rospy.Rate(1) # 10hz
    cntIter = 0
    while not rospy.is_shutdown() and cntIter < 2:
    #only send a single joint movement, the rest is set to 0
      hello_str = "Publish a trajectory %s" % rospy.get_time()
      rospy.loginfo(hello_str)
    #prepare a trajectory

      jointNr = 43
      mat = Float64MultiArray()
      mat.layout.dim = []
      #mat.data = [30.0]*jointNr
      mat.data = JointStates
 
      print(mat.data)
  
      pub.publish(mat)

      print(mat)
      cntIter += 1
      rate.sleep()



if __name__ == '__main__':
    say_and_print('Hello, please guess this pantomime')
    movements = ['kick', 'shake', 'nod']

    while True:
        for move in random.sample(movements, len(movements)):
            guess_game(move) #guess_game(move)


#if __name__ == '__main__':
 #   try:
#        sendTrajectory()
#    except rospy.ROSInterruptException:
#        pass

