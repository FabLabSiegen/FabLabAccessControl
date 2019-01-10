#include <ArduinoJson.h>

//WiFi imports
#include <ESP8266WiFi.h>

//MQTT imports
#include <PubSubClient.h>

//RFID imports
#include "MFRC522.h"
#define RST_PIN 15 // D8 RST-PIN for RC522 - RFID - SPI - Modul GPIO15 
#define SS_PIN  2  // D4 SDA-PIN for RC522 - RFID - SPI - Modul GPIO4 auf huzzah
//SCK GPIO 14 D5
//MISO GPIO 12 D6
//MOSI GPIO 13 D7

DynamicJsonBuffer jsonBuffer;

//WLAN Status LED
//leuchtet wenn verbunden
//blinkt wenn verbinden
//aus wenn nicht verbunden
const int WLAN_LED = 16; // D0
//MQTT Status LED
//blinkt 2 x wenn gesendet wird
//leuchtet wenn verbunden
//blinkt wenn verbinden
//aus wenn nicht verbunden
const int MQTT_LED = 5; // D1
//Status LED
//aus wenn niemand angemeldet
//an wenn angemeldet
//blinkt wenn anmelden
const int STATUS_LED = 4; // D2

//aktueller status
byte LOGIN_STATUS = 0;
//0	abgemeldet
//1	anmelden
//2	angemeldet
//3	abmelden

//MAC Adresse des Wifi Moduls
String WLAN_MAC;

//Logout Button
const int LOGOUT_BUTTON = 0; //D3

//WLAN zugangsdaten
// WARNING add credentials
const char* ssid = "";
const char* password = "";

//MQTT server
// WARNING add credentials
const char* mqtt_server = "";
const char* mqtt_user = "";
const char* mqtt_password = "";
const String mqtt_client = "FabLab-ESP";
//WLAN_MAC/status wird an den sub topic angehängt
//WLAN_MAC/cmd wird an den pub topic angehängt
const String mqtt_pub = "FabLab/";
const String mqtt_sub = "FabLab/";

//MQTT init
WiFiClient espClient;
PubSubClient client(espClient);
//MQTT vars
long lastMsg = 0;
char msg[50];

//RFID init
MFRC522 mfrc522(SS_PIN, RST_PIN);

//lässt die led auf pin times * blinken mit einem wait delay
void flash_LED(int pin, int times, int wait) {

  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(wait);
    digitalWrite(pin, LOW);

    if (i + 1 < times) {
      delay(wait);
    }
  }
}

void dump_byte_array(byte *buffer, byte bufferSize) {
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], HEX);
  }
}

//wandelt rfid uuid von byte pointer nach string
String uuid_to_string(byte *buffer, byte bufferSize) {
  String out = "";
  for (byte i = 0; i < bufferSize; i++) {
    if (buffer[i] < 0x10) out += "0";
    out += String(buffer[i], HEX);
  }
  return out;
}

//wandelt mac adresse von byte array nach string
String mac_to_string(byte buffer[6]) {
  String out = "";
  for (int i = 5; i > -1; i--) {
    if (buffer[i] < 0x10) out += "0";
    out += String(buffer[i], HEX);
  }
  return out;
}

//interrupt routine für logout button
//in interrupt routinen den code klein halten
void LOGOUTLOW() {
  Serial.println("Knopf gedrückt");
  //setze STATUS auf abmelden wenn angemeldet
  if (LOGIN_STATUS == 2) {
    Serial.println("Melde ab....");
    LOGIN_STATUS = 3;
  }
}

//verbindet mit wifi
//blockt bis wifi verbunden
void setup_wifi() {

  digitalWrite(WLAN_LED, LOW);
  delay(10);
  Serial.println();
  Serial.print("Starte WLAN Verbindung mit SSID ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  WiFi.mode(WIFI_STA); //deactivate AP-mode (default is WIFI_AP_STA)
  flash_LED(WLAN_LED, 2, 250);
  while (WiFi.status() != WL_CONNECTED) {
    //delay(500);
    flash_LED(WLAN_LED, 2, 250);
    Serial.print(".");
  }

  //verbunden, LED einschalten, Info ausgeben
  digitalWrite(WLAN_LED, HIGH);
  Serial.println("");
  Serial.println("WLAN verbunden!");
  Serial.println("IP Addresse: ");
  Serial.println(WiFi.localIP());

  Serial.println("");
  byte mac[6];
  WiFi.macAddress(mac);
  Serial.print("MAC Addresse: ");
  Serial.print(mac[5], HEX);
  Serial.print(":");
  Serial.print(mac[4], HEX);
  Serial.print(":");
  Serial.print(mac[3], HEX);
  Serial.print(":");
  Serial.print(mac[2], HEX);
  Serial.print(":");
  Serial.print(mac[1], HEX);
  Serial.print(":");
  Serial.println(mac[0], HEX);
  WLAN_MAC = mac_to_string(mac);
  Serial.print("WLAN_MAC : ");
  Serial.println(WLAN_MAC);
  
}

//callback prozedur für MQTT subscribe
//wird durchlaufen sobald eine nachricht anliegt 
void callback(char* topic, byte* payload, unsigned int length) {
  
  String msg = "";
  for (int i = 0; i < length; i++) {
    //Serial.print((char)payload[i]);
    msg += (char)payload[i];
  }

  Serial.print("MQTT Nachricht empfangen : ");
  Serial.print(msg);
  Serial.println();
  Serial.print("Aktueller Status : ");
  Serial.print(LOGIN_STATUS);
  Serial.println();

  JsonObject& data = jsonBuffer.parseObject(msg);
  
  //STATUS ist auf abmelden und abmeldung bestätigt
  if (LOGIN_STATUS == 3 && data["cmd"] == "0") {
    digitalWrite(STATUS_LED, LOW);
    Serial.println("Logout erfolgreich!");
    LOGIN_STATUS = 0;
    delay(5000);
  //STATUS ist auf abmelden und abmeldung nicht bestätigt
  } else if (LOGIN_STATUS == 3 && data["cmd"] != "0") {
    flash_LED(STATUS_LED, 5, 100);
    digitalWrite(STATUS_LED, HIGH);
    Serial.println("Logout nicht erfolgreich!");
    LOGIN_STATUS = 2;
  //STATUS ist auf anmelden und anmeldung bestätigt
  } else if (LOGIN_STATUS == 1 && data["cmd"] == "2") {
    digitalWrite(STATUS_LED, HIGH);
    Serial.println("Login erfolgreich!");    
    LOGIN_STATUS = 2;
  //STATUS ist auf anmelden und anmeldung nicht bestätigt  
  } else if (LOGIN_STATUS == 1 && data["cmd"] == "0") {
    flash_LED(STATUS_LED, 5, 100);
    digitalWrite(STATUS_LED, LOW);
    Serial.println("Login nicht erfolgreich!");    
    LOGIN_STATUS = 0;
    //STATUS ist abgemeldet und bekommen anmeldung  
  } else if (LOGIN_STATUS == 0 && data["cmd"] == "2") {
    flash_LED(STATUS_LED, 5, 100);
    digitalWrite(STATUS_LED, HIGH);
    Serial.println("Zwangsweise angemeldet!");    
    LOGIN_STATUS = 2;
    //STATUS ist angemeldet und bekommen zwangs abmeldung 
  } else if (LOGIN_STATUS == 2 && data["cmd"] == "0") {
    flash_LED(STATUS_LED, 5, 100);
    digitalWrite(STATUS_LED, LOW);
    Serial.println("Zwangsweise abgemeldet!");    
    LOGIN_STATUS = 0;
  }
}

//generic ESP setup
void setup() {
  //LED Pins OUTPUT setzen
  pinMode(WLAN_LED, OUTPUT);
  pinMode(MQTT_LED, OUTPUT);
  pinMode(STATUS_LED, OUTPUT);

  //serielle Ausgabe aktivieren
  Serial.begin(9600);
  Serial.println();
  Serial.println("Starte FabLab ESP");

  // Init SPI bus
  Serial.println("SPI Init...");
  SPI.begin();

  // Init MFRC522
  Serial.println("MFRC522 Init...");
  mfrc522.PCD_Init();

  //WLAN starten
  setup_wifi();

  //MQTT client init
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  //PUSHButton init
  pinMode(LOGOUT_BUTTON,  INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(LOGOUT_BUTTON), LOGOUTLOW, CHANGE);


  Serial.println(F("FabLab ESP setup ende...."));
  Serial.println(F("======================================================"));
}

//MQTT reconnect prozedur
//blockt bis verbunden!
void reconnect() {
  digitalWrite(MQTT_LED, LOW);

  //erstma testen ob wifi überhaupt geht
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("WLAN Verbindung abgebrochen...");
    setup_wifi();
  }

  while (!client.connected()) {
    Serial.print("Starte MQTT Verbindung...");

    flash_LED(MQTT_LED, 2, 250);
    //setze eindeutige mqtt client id
    // FabLab-ESP + WLAN_MAC
    String tmp = mqtt_client + WLAN_MAC;
    char c_id[tmp.length() + 1];
    tmp.toCharArray(c_id, tmp.length() + 1);

    if (client.connect(c_id, mqtt_user, mqtt_password)) {
      digitalWrite(MQTT_LED, HIGH);
      Serial.println("Verbunden mit MQTT Server!");

      //setze topic für eingehende nachrichten
      // /FabLab/ + WLAN_MAC + /status
      String tmp = mqtt_sub + WLAN_MAC + "/status";
      char topic[tmp.length() + 1];
      tmp.toCharArray(topic, tmp.length() + 1);
      Serial.print("Melde an Topic ");
      Serial.print(topic);
      Serial.println(" an!");
      client.subscribe(topic);      
    } else {
      //anmeldung fehlgeschlagen, gebe fehlermeldung aus
      digitalWrite(MQTT_LED, LOW);
      Serial.print("fehlgeschlagen : ");
      switch (client.state()) {
        case -4:
          Serial.print("MQTT_CONNECTION_TIMEOUT");
          break;
        case -3:
          Serial.print("MQTT_CONNECTION_LOST");
          break;
        case -2:
          Serial.print("MQTT_CONNECT_FAILED");
          break;
        case 1:
          Serial.print("MQTT_CONNECT_BAD_PROTOCOL");
          break;
        case 2:
          Serial.print("MQTT_CONNECT_BAD_CLIENT_ID");
          break;
        case 3:
          Serial.print("MQTT_CONNECT_UNAVAILABLE");
          break;
        case 4:
          Serial.print("MQTT_CONNECT_BAD_CREDENTIALS");
          break;
        case 5:
          Serial.print("MQTT_CONNECT_UNAUTHORIZED");
          break;
      }
      Serial.println(" versuche erneut in 5 Sekunden....");
      flash_LED(MQTT_LED, 20, 250);
    }
  }
}

void loop() {
  //wenn MQTT Client keine Verbindung dann reconnect....BLOCKING!!!!
  if (!client.connected()) {
    reconnect();
  }

  //eingehende MQTT Nachrichten verarbeiten  
  client.loop();

  //wenn kein RFID tag gefunden return zu loop begin
  if ( ! mfrc522.PICC_IsNewCardPresent()) {
    if (LOGIN_STATUS == 3) {
      flash_LED(STATUS_LED, 2, 100);
      digitalWrite(STATUS_LED, HIGH);
    } else {
      delay(200);
    }
    return;
  }
  
  //wenn RFID tag UUID nicht gelesen weden kann return zu loop begin
  if ( ! mfrc522.PICC_ReadCardSerial()) {
    delay(50);
    return;
  }
  
  //RFID tag erkannt und daten gelesen...
  Serial.print(F("RFID erkannt....UID : "));
  dump_byte_array(mfrc522.uid.uidByte, mfrc522.uid.size);
  Serial.println();
  
  String UUID = uuid_to_string(mfrc522.uid.uidByte, mfrc522.uid.size);
  //MQTT sende LOGIN wenn nicht angemeldet
  if (LOGIN_STATUS == 0) {    
    Serial.print("Schicke MQTT LOGIN : ");
    Serial.println(UUID);
    Serial.println();
    
    String tmp = mqtt_pub + WLAN_MAC + "/cmd";
    char topic[tmp.length() + 1];
    tmp.toCharArray(topic, tmp.length() + 1);

    tmp = "{\"cmd\":\"1\",\"data\":\"" + UUID + "\"}";
    char msg[tmp.length() + 1];
    tmp.toCharArray(msg, tmp.length() + 1);
    
    client.publish(topic, msg);
    flash_LED(STATUS_LED, 2, 250);

    //STATUS auf anmelden
    LOGIN_STATUS = 1;
  } else if (LOGIN_STATUS == 3) {
    //LOGIN_STATUS von interrupt routine auf abmelden gesetzt
    Serial.print("Schicke MQTT LOGOUT!");

    String tmp = mqtt_pub + WLAN_MAC + "/cmd";
    char topic[tmp.length() + 1];
    tmp.toCharArray(topic, tmp.length() + 1);

    tmp = "{\"cmd\":\"3\",\"data\":\"" + UUID + "\"}";
    char msg[tmp.length() + 1];
    tmp.toCharArray(msg, tmp.length() + 1);

    client.publish(topic, msg);
    flash_LED(STATUS_LED, 2, 250);
  } 
}


