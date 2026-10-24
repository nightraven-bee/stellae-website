import Foundation
import Vision

// Local OCR assistance only. Visual inspection is still required.
let directory = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2])
let files = try FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension.lowercased() == "png" }
    .sorted { $0.lastPathComponent < $1.lastPathComponent }
var rows: [[String: Any]] = []
for file in files {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(url: file, options: [:]).perform([request])
    let text = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
    let keys = ["舟", "经济压力", "语气平静", "富途", "微信支付", "员工管理", "星黎OS", "星黎 OS", "Stellae Room"]
    let flags = keys.filter { text.localizedCaseInsensitiveContains($0) }
    let phone = text.range(of: "(?<![0-9])1[3-9][0-9]{9}(?![0-9])", options: .regularExpression) != nil
    rows.append(["file": file.lastPathComponent, "keyword_flags": flags, "phone_pattern": phone, "text": text])
}
let result: [String: Any] = ["method": "Apple Vision OCR on exported media samples; complements visual inspection", "sample_count": rows.count, "files": rows]
let data = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
try data.write(to: output)
let flagged = rows.filter { !($0["keyword_flags"] as! [String]).isEmpty || ($0["phone_pattern"] as! Bool) }.count
print("OCR samples: \(rows.count), flagged: \(flagged)")
