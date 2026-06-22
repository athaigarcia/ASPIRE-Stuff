const int transistor = 8;

void setup()
{
  pinMode (transistor,  OUTPUT);
  digitalWrite(transistor, HIGH);
}

void loop()
{
  if (Serial.available()) {
  char c = Serial.read();
  if (c == '1') {
    digitalWrite(transistor, LOW);
  }
  else if (c == '0') {
    digitalWrite(transistor, HIGH);
  }
  
}

}
