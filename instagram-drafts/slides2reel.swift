import Foundation
import AVFoundation
import AppKit
import CoreGraphics

let args = CommandLine.arguments
guard args.count >= 3 else {
    fputs("usage: slides2reel out.mp4 [--end end.jpg] img...\n", stderr)
    exit(1)
}
let outURL = URL(fileURLWithPath: args[1])
var endURL: URL? = nil
var images: [URL] = []
var i = 2
while i < args.count {
    if args[i] == "--end", i + 1 < args.count {
        endURL = URL(fileURLWithPath: args[i + 1])
        i += 2
        continue
    }
    images.append(URL(fileURLWithPath: args[i]))
    i += 1
}
guard !images.isEmpty else { fputs("no images\n", stderr); exit(1) }
try? FileManager.default.removeItem(at: outURL)

let w = 1080, h = 1350
let secondsPerSlide = 1.8
let endSeconds = 4.5
let fps = 30.0
let frameDuration = CMTime(seconds: 1.0 / fps, preferredTimescale: 600)

let writer = try AVAssetWriter(outputURL: outURL, fileType: .mp4)
writer.shouldOptimizeForNetworkUse = true
let videoSettings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: w,
    AVVideoHeightKey: h,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: 8_000_000,
        AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
    ],
]
let videoInput = AVAssetWriterInput(mediaType: .video, outputSettings: videoSettings)
videoInput.expectsMediaDataInRealTime = false
let attrs: [String: Any] = [
    kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32ARGB),
    kCVPixelBufferWidthKey as String: w,
    kCVPixelBufferHeightKey as String: h,
]
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: videoInput, sourcePixelBufferAttributes: attrs)
writer.add(videoInput)
writer.startWriting()
writer.startSession(atSourceTime: .zero)

var t = CMTime.zero
func appendImage(_ imgURL: URL, seconds: Double) {
    guard let ns = NSImage(contentsOf: imgURL),
          let cg = ns.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        fputs("bad image \(imgURL.path)\n", stderr); exit(1)
    }
    let frames = Int((seconds * fps).rounded())
    for _ in 0..<frames {
        while !videoInput.isReadyForMoreMediaData { Thread.sleep(forTimeInterval: 0.002) }
        var pb: CVPixelBuffer?
        CVPixelBufferCreate(kCFAllocatorDefault, w, h, kCVPixelFormatType_32ARGB, nil, &pb)
        guard let buf = pb else { continue }
        CVPixelBufferLockBaseAddress(buf, [])
        let ctx = CGContext(
            data: CVPixelBufferGetBaseAddress(buf),
            width: w, height: h,
            bitsPerComponent: 8,
            bytesPerRow: CVPixelBufferGetBytesPerRow(buf),
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue
        )!
        ctx.interpolationQuality = .high
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
        CVPixelBufferUnlockBaseAddress(buf, [])
        adaptor.append(buf, withPresentationTime: t)
        t = CMTimeAdd(t, frameDuration)
    }
}
for img in images { appendImage(img, seconds: secondsPerSlide) }
if let endURL = endURL { appendImage(endURL, seconds: endSeconds) }
videoInput.markAsFinished()
writer.endSession(atSourceTime: t)
let sem = DispatchSemaphore(value: 0)
writer.finishWriting { sem.signal() }
sem.wait()
if writer.status != .completed {
    fputs("writer \(String(describing: writer.error))\n", stderr)
    exit(1)
}
print("wrote \(outURL.path) dur=\(CMTimeGetSeconds(t))")
