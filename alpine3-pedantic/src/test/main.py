from ctypes import *
import os
import sys
import RandomNumberGenerator
import Voter1
import Voter2
import Voter3
import Integration
import socket
import subprocess
import time

voterLibFile = os.getcwd()+'/phis.so'

class sensor_t(Structure):
    _fields_ = [("state", c_uint),
                   ("reading", c_uint8)]

Uint8Array3 = c_uint8 * 3
Uint8Array4 = c_uint8 * 4
SensorArray3 = sensor_t * 3

def runVoterA(voterLib, sensor1, sensor2, sensor3) -> bool:
    '''
    run c implementation of voterA with sensor1-3 as input and returns its output
    voterLib represents the shared object file containing the c functions
    '''
    sensorMsg = Uint8Array4(sensor1, sensor2, sensor3, 0)
    sensorReadings = SensorArray3()
    voterResult = c_bool()
    flowcontrol = c_uint32(0)
    voterLib.evaluateSensors(sensorMsg, sensorReadings)
    voterLib.evaluateDistance_BlockA(sensorReadings, pointer(voterResult), pointer(flowcontrol))
    if voterResult:
        return True
    else:
        return False

def testVoterA(voterLib, logFile) -> bool:
    '''
    Test voterA with 3 random values for 3 sensors
    Returns test result
    '''
    sensor1 = RandomNumberGenerator.RandNum()[0]
    sensor2 = RandomNumberGenerator.RandNum()[1]
    sensor3 = RandomNumberGenerator.RandNum()[2]
    # print([sensor1, sensor2, sensor3])
    expectedResult = not Voter1.voter1([sensor1, sensor2, sensor3])
    voterResult = runVoterA(voterLib, sensor1, sensor2, sensor3)
    if voterResult == expectedResult:
        return True
    else:
        logFile.write(f"Sensor values: ({sensor1}, {sensor2}, {sensor3}), Voter A returned {voterResult}, expected {expectedResult}\n")
        return False

def runVoterB(voterLib, sensor1, sensor2, sensor3) -> bool:
    '''
    run c implementation of voterB with sensor1-3 as input and returns its output
    voterLib represents the shared object file containing the c functions
    '''
    sensorMsg = Uint8Array4(sensor1, sensor2, sensor3, 0)
    sensorReadings = SensorArray3()
    voterResult = c_bool()
    flowcontrol = c_uint32(0)
    voterLib.evaluateSensors(sensorMsg, sensorReadings)
    voterLib.evaluateDistance_BlockB(sensorReadings, pointer(voterResult), pointer(flowcontrol))
    if voterResult:
        return True
    else:
        return False

def testVoterB(voterLib, logFile) -> bool:
    '''
    Test voterB with 3 random values for 3 sensors
    Returns test result
    '''
    sensor1 = RandomNumberGenerator.RandNum()[0]
    sensor2 = RandomNumberGenerator.RandNum()[1]
    sensor3 = RandomNumberGenerator.RandNum()[2]
    # print([sensor1, sensor2, sensor3])
    expectedResult = not Voter2.voter2([sensor1, sensor2, sensor3])
    voterResult = runVoterB(voterLib, sensor1, sensor2, sensor3)
    if voterResult == expectedResult:
        return True
    else:
        logFile.write(f"Sensor values: ({sensor1}, {sensor2}, {sensor3}), Voter B returned {voterResult}, expected {expectedResult}\n")
        return False

def testVoter3(voterLib, logFile, input1, input2) -> bool:
    '''
    Test Stage2Voter with every possible input
    Returns test result
    '''
    enterSafeState = c_bool(True)
    flowcontrol = c_uint32(0)
    expectedResult = Voter3.voter3(input1, input2)
    voterResult = voterLib.runStage2Voter(input1, input2, pointer(enterSafeState), pointer(flowcontrol))
    # print(f"Input for voter3: {input1}, {input2}")
    if bool(enterSafeState) == expectedResult:
        # print("Outcome of Voter 3 matched expected result")
        return True
    else:
        # print("Outcome of Voter 3 didn't match expected result")
        logFile.write(f"Voter 1 and 2 inputs: ({input1}, {input2}), Stage2Voter returned {voterResult}, expected {expectedResult}\n")
        return False

def runSystem(sensor1, sensor2, sensor3, process) -> bool:
    '''
    Gives 3 sensor values to the c-program and fetch its output
    '''
    input = Uint8Array3(sensor1, sensor2, sensor3)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        addr = ("127.0.0.1", 8080)
        s.sendto(input, addr)
    output = process.stdout.readlines(1)
    if output == [b'Go To Safe State: TRUE\n']:
        return True
    elif output == [b'Go To Safe State: FALSE\n']:
        return False
    else:
        print("Did not expect this result:")
        print(output)
        process.stdin.write(b'q\n')
        sys.exit(-1)

def testIntegration(voterLib, logFile, process, numTestsIntegration) -> bool:
    '''
    Tests the entire system / integration of all voters by using a golden Model
    and random inputs
    '''
    global lastOutcome
    sensor1 = RandomNumberGenerator.RandNum()[0]
    sensor2 = RandomNumberGenerator.RandNum()[1]
    sensor3 = RandomNumberGenerator.RandNum()[2]
    # print([sensor1, sensor2, sensor3])
    ImplementationResult = runSystem(sensor1, sensor2, sensor3, process)
    expectedResult = Integration.Integration(sensor1, sensor2, sensor3)
    if ImplementationResult == expectedResult:
        return True
    else:
        logFile.write(f"{numTestsIntegration}: Sensor values: ({sensor1}, {sensor2}, {sensor3}), last State: {lastOutcome}, Implementation returned {ImplementationResult}, expected {expectedResult}\n")
        return False

def main() -> int:
    '''
    Run all verification tests and output the results
    '''
    numFailedTestsVoterA = 0
    numTestsVoterA = 0
    numFailedTestsVoterB = 0
    numTestsVoterB = 0
    numFailedTestsVoter3 = 0
    numTestsVoter3 = 0
    numFailedTestsIntegration = 0
    numTestsIntegration = 0
    voterLib = CDLL(voterLibFile)
    logFile = open("../results_test.txt", 'w')

    TEST_ITERATION = 10000000

    # unit test voter A
    print("Testing voter A ...")
    logFile.write("Failed Tests for voter A:\n")
    for _ in range(TEST_ITERATION):
        if testVoterA(voterLib, logFile):
            numTestsVoterA = numTestsVoterA + 1
        else:
            numFailedTestsVoterA = numFailedTestsVoterA + 1
            numTestsVoterA = numTestsVoterA + 1

    # unit test voter B
    print("Testinig voter B ...")
    logFile.write("Failed Tests for voter B:\n")
    for _ in range(TEST_ITERATION):
        if testVoterB(voterLib, logFile):
            numTestsVoterB = numTestsVoterB + 1
        else:
            numFailedTestsVoterB = numFailedTestsVoterB+ 1
            numTestsVoterB = numTestsVoterB + 1


    # unit test voter 3
    print("Testing stage2voter ...")
    logFile.write("Failed Tests for voter 3:\n")
    if testVoter3(voterLib, logFile, True, True):
        numTestsVoter3 = numTestsVoter3 + 1
    else:
        numFailedTestsVoter3 = numFailedTestsVoter3+ 1
        numTestsVoter3 = numTestsVoter3 + 1

    if testVoter3(voterLib, logFile, False, True):
        numTestsVoter3 = numTestsVoter3 + 1
    else:
        numFailedTestsVoter3 = numFailedTestsVoter3+ 1
        numTestsVoter3 = numTestsVoter3 + 1

    if testVoter3(voterLib, logFile, True, False):
        numTestsVoter3 = numTestsVoter3 + 1
    else:
        numFailedTestsVoter3 = numFailedTestsVoter3+ 1
        numTestsVoter3 = numTestsVoter3 + 1

    if testVoter3(voterLib, logFile, False, False):
        numTestsVoter3 = numTestsVoter3 + 1
    else:
        numFailedTestsVoter3 = numFailedTestsVoter3+ 1
        numTestsVoter3 = numTestsVoter3 + 1

    # system / integration test
    # print("Test System/ Integration:")
    print("Testing system ...")
    logFile.write("Failed Tests for System/ Integration Test:\n")
    p = subprocess.Popen("./phis_test", stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    for _ in range(TEST_ITERATION):
        if testIntegration(voterLib, logFile, p, numTestsIntegration):
            numTestsIntegration = numTestsIntegration+ 1
        else:
            numFailedTestsIntegration = numFailedTestsIntegration + 1
            numTestsIntegration = numTestsIntegration+ 1
        # print(f"{numTestsIntegration} from {TEST_ITERATION}")
    p.stdin.write(b'q\n')

    # prints for Voter A
    print(f"Test Voter A: {numFailedTestsVoterA} from {numTestsVoterA} tests failed")
    logFile.write(f"\nTest Voter A: {numFailedTestsVoterA} from {numTestsVoterA} tests failed\n")

    # prints for Voter B
    print(f"Test Voter B: {numFailedTestsVoterB} from {numTestsVoterB} tests failed")
    logFile.write(f"Test Voter B: {numFailedTestsVoterB} from {numTestsVoterB} tests failed\n")

    # prints for Voter 3
    print(f"Test Voter 3: {numFailedTestsVoter3} from {numTestsVoter3} tests failed")
    logFile.write(f"Test Voter 3: {numFailedTestsVoter3} from {numTestsVoter3} tests failed\n")

    # prints for System / Integration Test
    if (numFailedTestsIntegration == 0):
        print(f"System/ Integration Test: All tests passed (With {numTestsIntegration} tests in total)")
        logFile.write(f"System/ Integration Test: All tests passed (With {numTestsIntegration} tests in total)\n\n")
    else:
        print(f"System/ Integration Test: {numFailedTestsIntegration} from {numTestsIntegration} tests failed")
        logFile.write(f"System/ Integration Test: {numFailedTestsIntegration} from {numTestsIntegration} tests failed\n\n")

    # prints for total
    numFailedTestsTotal = numFailedTestsVoterA + numFailedTestsVoterB + numFailedTestsVoter3 + numFailedTestsIntegration
    numTestsTotal = numTestsVoterA + numTestsVoterB + numTestsVoter3 + numTestsIntegration

    if (numFailedTestsTotal == 0):
        print(f"Summary: All tests passed (With {numTestsTotal} tests in total)")
        logFile.write(f"Summary: All tests passed (With {numTestsTotal} tests in total)")
    else:
        print(f"Summary: {numFailedTestsTotal} from {numTestsTotal} tests failed")
        logFile.write(f"Summary: {numFailedTestsTotal} from {numTestsTotal} tests failed")
    return numFailedTestsTotal

if __name__ == "__main__":
    sys.exit(main())
