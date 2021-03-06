 char message[30];
 int fieldIndex = 0;
  
 void setup(){
  Serial.begin(9600);
}

void loop() {

  if(Serial.available()){
    char ch = Serial.read();
    if(ch == 10 ) {
      message[fieldIndex] = 0;
      Serial.println(message);
      message[0] = 0; // ready to start over
      fieldIndex = 0;
    } else {
      message[fieldIndex] = ch;
      fieldIndex++; 
    } 
  }
  /*Serial.print("A");
  Serial.print(126);
  Serial.print("");
  Serial.print("");
  Serial.println();
  delay(1000);*/
}
