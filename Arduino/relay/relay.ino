const int RELAY_PIN = 4;
int x;
void setup() {

  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  Serial.setTimeout(1);
  delay(100);
}

//Main loop
void loop() {
  x = Serial.readString().toInt();
  Serial.flush();
  if (x == 3) {
    digitalWrite(RELAY_PIN, HIGH);//ON
    Serial.write("HIGH\n");
  }
  if (x == 4){
    digitalWrite(RELAY_PIN, LOW);//OFF
    Serial.write("LOW\n");
  }
 }
