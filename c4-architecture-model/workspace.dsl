workspace "Smart Speaker" "Description"

    !identifiers hierarchical

    model {
        u = person "Office User"
        d = person "Admin"
        ss = softwareSystem "Smart Speaker" "Fully offline. Hardware: Orange Pi 5. Provides customers Task and Schedule Management tools." {
            tags "Smart Speaker"
            rh = container "Rhasspy API" "Provides Wake Word Detection, STT and TTS transitions, Intent Handling and Profile Management." "Docker"
            mqtt = container "MQTT Brocker" "Message Brocker." "Mosquitto"
            bs = container "Python Backend Service" "Provides Intent Execution." "Python" {
                mqtt_client = component "MQTT Client" "Recives Rhasspy’s JSON output." "paho-mqtt"
                rout = component "Intent Router" "Extracts the intent, parametrs and siteID. Defined intents to postponed/non-postponed event." "Python"
                post = component "Postponed" "Process postponed events (e.g., timers, calendar-event)" "Python"
                nonpost = component "Non-Postponed" "Process instatnt intents (e.g., \"What time is it?\")" "Python"
                eventcheck = component "EventChecker" "Checks if an event has occurred." "Python"
            }
            db = container "Database" "Stores Intent data and logs." "sqlite" { 
                tags "Database" 
            }
        }
        cn = softwareSystem "Company Network" "Has access to Internet. Stores information that updates over time."
        
        u -> ss "Voice Commands"
        d -> ss "Updates and configurates"
        ss -> cn "Gets information using"
        
        ss.rh -> ss.mqtt "Reads from and writes to"
        ss.mqtt -> ss.rh "Reads from and writes to"
        ss.mqtt -> ss.bs "Process recognized intents using"
        ss.bs -> ss.db "Reads from and writes to"
        ss.bs -> cn "Reads from and writes to"

        ss.mqtt -> ss.bs.mqtt_client "Sends recognized intent to" "JSON/MQTT"
        ss.bs.mqtt_client -> ss.bs.rout "Process Intent"
        ss.bs.rout -> ss.bs.post "Uses"
        ss.bs.rout -> ss.bs.nonpost "Uses"
        ss.bs.eventcheck -> ss.bs.post "Periodically asks for an event to be performed"
        ss.bs.post -> ss.bs.eventcheck "Responds to check"
        ss.bs.post -> ss.mqtt "Sends response data to"
        ss.bs.nonpost -> ss.mqtt "Sends response data to"
        
        u -> ss.rh "Interacts through recordered voice commands."
        d -> ss.rh "Configurates Rhasspy API through JSON.config"
        
    }

    views {
        systemContext ss "Diagram1" {
            include *
            autolayout lr
        }

        container ss "Diagram2" {
            include *
            # autolayout lr
        }
        
        component ss.bs "Diagram3" {
            include *
            # autolayout lr
        }
        
        styles {
            element "Element" {
                color white
            }
            element "Person" {
                background #07427a
                shape person
            }
            element "Software System" {
                background #999999
            }
            element "Smart Speaker" {
                background #2c6cad
            }
            element "Container" {
                background #2c6cad
            }
            element "Component" {
                background #2c6cad
            }
            element "Database" {
                shape cylinder
            }
        }
    }
}