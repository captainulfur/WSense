// WallSense - Aşama 1
// macOS: client'ın Wi-Fi kartından sinyal gücünü (RSSI) okur ve her ölçümü
// bir satır JSON olarak stdout'a yazar. server.py bu çıktıyı okur.
// Linux ve Windows için aynı işi rssi_reader.py yapar.
//
// Kullanım: rssi_reader [aralık_ms]   (varsayılan 100 ms = saniyede 10 ölçüm)

import CoreWLAN
import Foundation

setvbuf(stdout, nil, _IOLBF, 0)

let intervalMs = CommandLine.arguments.count > 1 ? (Int(CommandLine.arguments[1]) ?? 100) : 100

guard let iface = CWWiFiClient.shared().interface() else {
    FileHandle.standardError.write("Wi-Fi arayüzü bulunamadı\n".data(using: .utf8)!)
    exit(1)
}

while true {
    let t = Date().timeIntervalSince1970
    let rssi = iface.rssiValue()
    let noise = iface.noiseMeasurement()
    let channel = iface.wlanChannel()?.channelNumber ?? -1
    // rssi == 0 genelde "bağlı değil" demektir
    print("{\"t\":\(t),\"rssi\":\(rssi),\"noise\":\(noise),\"ch\":\(channel)}")
    usleep(useconds_t(intervalMs * 1000))
}
