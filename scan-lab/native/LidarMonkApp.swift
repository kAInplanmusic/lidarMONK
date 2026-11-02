import SwiftUI
import PhotosUI
import ImageIO
import AVFoundation
import UniformTypeIdentifiers
import CoreImage
import UIKit

@main
struct LidarMonkApp: App {
    var body: some Scene { WindowGroup { ContentView() } }
}

struct ContentView: View {
    @State private var showingPicker = false
    @State private var shareURL: URL?
    @State private var status = "Wähle ein Originalfoto aus deiner Mediathek."
    @State private var busy = false
    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 20) {
                Text("lidarMONK").font(.largeTitle.bold())
                Text("Tiefendaten-Exporter").font(.title2)
                Text("Prüft ein Foto auf eingebettete Tiefen- oder Disparitätsdaten und exportiert auslesbare metrische Werte für das Scan Lab. Die Herkunft vom LiDAR-Sensor wird nicht bestätigt.")
                    .foregroundStyle(.secondary)
                Button("Originalfoto auswählen") { showingPicker = true }.buttonStyle(.borderedProminent).disabled(busy)
                if busy { ProgressView("Analysiere …") }
                Text(status).font(.callout).textSelection(.enabled)
                if let url = shareURL { ShareLink(item: url) { Label("Tiefenpaket teilen oder speichern", systemImage: "square.and.arrow.up") }.buttonStyle(.bordered) }
                Spacer()
                Text("Videos werden nicht unterstützt. Die ausgewählte Fotodatei muss die Tiefenkarte tatsächlich enthalten. Export oder Weitergabe können Zusatzdaten entfernen.").font(.footnote).foregroundStyle(.secondary)
            }.padding().navigationTitle("Scan Lab")
            .sheet(isPresented: $showingPicker) { ImagePicker { url in
                guard let url else { status = "Keine Datei übernommen."; return }
                busy = true; status = "Analysiere …"; shareURL = nil
                DispatchQueue.global(qos: .userInitiated).async {
                    defer { try? FileManager.default.removeItem(at: url) }
                    do {
                        let result = try DepthExporter.export(url)
                        DispatchQueue.main.async { shareURL = result.url; status = "Tiefenkarte exportiert: \(result.width) × \(result.height) Pixel. Als Datei sichern und im Scan Lab öffnen."; busy = false }
                    } catch {
                        DispatchQueue.main.async { status = error.localizedDescription; busy = false }
                    }
                }
            }}
        }
    }
}

struct ImagePicker: UIViewControllerRepresentable {
    let completion: (URL?) -> Void
    func makeCoordinator() -> Coordinator { Coordinator(completion) }
    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration(photoLibrary: .shared())
        config.filter = .images; config.selectionLimit = 1; config.preferredAssetRepresentationMode = .current
        let picker = PHPickerViewController(configuration: config); picker.delegate = context.coordinator
        return picker
    }
    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}
    final class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let completion: (URL?) -> Void
        init(_ completion: @escaping (URL?) -> Void) { self.completion = completion }
        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            picker.dismiss(animated: true)
            guard let provider = results.first?.itemProvider else { completion(nil); return }
            guard let type = provider.registeredTypeIdentifiers.first(where: { UTType($0)?.conforms(to: .image) == true }) else { completion(nil); return }
            provider.loadFileRepresentation(forTypeIdentifier: type) { url, _ in
                guard let url else { DispatchQueue.main.async { self.completion(nil) }; return }
                let dest = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + "." + (url.pathExtension.isEmpty ? "img" : url.pathExtension))
                do { try FileManager.default.copyItem(at: url, to: dest); DispatchQueue.main.async { self.completion(dest) } }
                catch { DispatchQueue.main.async { self.completion(nil) } }
            }
        }
    }
}

enum ExportError: LocalizedError {
    case cannotOpen, noDepth, conversion, image, tooLarge
    var errorDescription: String? {
        switch self {
        case .cannotOpen: return "Die Bilddatei konnte nicht geöffnet werden."
        case .noDepth: return "Keine auslesbare Tiefen- oder Disparitätskarte gefunden. Das beweist nicht, dass die ursprüngliche Aufnahme nie eine Karte hatte; sie kann beim Export verloren gegangen sein."
        case .conversion: return "Die Zusatzdaten konnten nicht in metrische Tiefe umgewandelt werden."
        case .image: return "Das Farbbild konnte nicht exportiert werden."
        case .tooLarge: return "Die Tiefenkarte ist zu groß für dieses Testformat."
        }
    }
}

enum DepthExporter {
    static func export(_ url: URL) throws -> (url: URL, width: Int, height: Int) {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else { throw ExportError.cannotOpen }
        let depthInfo = CGImageSourceCopyAuxiliaryDataInfoAtIndex(source, 0, kCGImageAuxiliaryDataTypeDepth)
        let disparityInfo = CGImageSourceCopyAuxiliaryDataInfoAtIndex(source, 0, kCGImageAuxiliaryDataTypeDisparity)
        guard let info = depthInfo ?? disparityInfo else { throw ExportError.noDepth }
        let original = try AVDepthData(fromDictionaryRepresentation: info as! [AnyHashable: Any])
        // A conversion can fail to yield meaningful metric data if calibration is absent.
        guard original.depthDataAccuracy == .absolute else { throw ExportError.conversion }
        let depth = original.converting(toDepthDataType: kCVPixelFormatType_DepthFloat32)
        let map = depth.depthDataMap
        guard CVPixelBufferGetPixelFormatType(map) == kCVPixelFormatType_DepthFloat32 else { throw ExportError.conversion }
        let w = CVPixelBufferGetWidth(map), h = CVPixelBufferGetHeight(map)
        guard w > 0, h > 0, w * h <= 2_000_000 else { throw ExportError.tooLarge }
        CVPixelBufferLockBaseAddress(map, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(map, .readOnly) }
        guard let base = CVPixelBufferGetBaseAddress(map) else { throw ExportError.conversion }
        let stride = CVPixelBufferGetBytesPerRow(map)
        var values: [Any] = []; values.reserveCapacity(w * h)
        var valid = 0
        for y in 0..<h {
            let row = base.advanced(by: y * stride).assumingMemoryBound(to: Float32.self)
            for x in 0..<w {
                let v = row[x]
                if v.isFinite && v > 0 { values.append(Double(v)); valid += 1 }
                else { values.append(NSNull()) }
            }
        }
        guard valid > 0 else { throw ExportError.conversion }
        // Keep source pixel orientation; full calibration/orientation matching remains experimental.
        guard let cg = CGImageSourceCreateImageAtIndex(source, 0, nil), let jpeg = UIImage(cgImage: cg).jpegData(compressionQuality: 0.72) else { throw ExportError.image }
        let packet: [String: Any] = ["format":"lidarMONK-depth-v1", "width":w, "height":h,
            "depthMeters":values, "imageJPEGBase64":jpeg.base64EncodedString(),
            "sourceDepthType": depthInfo != nil ? "depth" : "disparity-converted",
            "projection": "estimated-60-degree-horizontal-fov", "sensorOrigin":"unknown"]
        let bytes = try JSONSerialization.data(withJSONObject: packet)
        let out = FileManager.default.temporaryDirectory.appendingPathComponent("lidarMONK-\(UUID().uuidString).json")
        try bytes.write(to: out, options: .atomic)
        return (out, w, h)
    }
}
