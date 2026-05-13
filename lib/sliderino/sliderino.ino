/*
sliderUSBOut()
When serial is available, the arduino will print a time stamp and 12-bit potentiometer position at the sampling rate.
Eatai Roth, 2017
*/

const int analogInPin = A0;  // Analog input pin that the potentiometer is attached to

//unsigned int sensorValue;        // value read from the pot
float startTime;
union{float asFloat; byte asBytes[4];}t;
union{unsigned int asUInt; byte asBytes[4];}sensorValue;
char serInput;

void setup() {
  // initialize serial communications:
  SerialUSB.begin(115200);
  while(!Serial);
  
  analogReadResolution(12);

  startTime = micros();
  t.asFloat = 0;
}

void loop() {
  if (SerialUSB.available()){
    serInput = SerialUSB.read();

    // If read value is 'g', serial is expecting Data to be written
    if (serInput == 0x67){
      t.asFloat = (micros()-startTime)/1000000.0; 
      sensorValue.asUInt = analogRead(analogInPin);
      SerialUSB.write(t.asBytes, 4);
      SerialUSB.write(sensorValue.asBytes, 4);
    }

    // If read value is 'a', restart timer
    else if (serInput == 0x61){
      //clearUSBRecBuffer();
      startTime = micros();
    }
}

//void clearUSBRecBuffer(){
//  while(SerialUSB.available()){
//    SerialUSB.read();
//  }
}
