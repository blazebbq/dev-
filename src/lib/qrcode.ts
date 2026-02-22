import QRCode from "qrcode";
import path from "path";
import fs from "fs/promises";

/**
 * Generates a QR code image for a machine page URL and saves it to /public/qrcodes.
 * Returns the public path (e.g. /qrcodes/machine-abc123.png).
 */
export async function generateMachineQRCode(
  gymSlug: string,
  machineId: string
): Promise<string> {
  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
  const machineUrl = `${appUrl}/g/${gymSlug}/machine/${machineId}`;

  // Ensure output directory exists
  const qrcodesDir = path.join(process.cwd(), "public", "qrcodes");
  await fs.mkdir(qrcodesDir, { recursive: true });

  const filename = `machine-${machineId}.png`;
  const filePath = path.join(qrcodesDir, filename);

  // Generate QR code as PNG file
  await QRCode.toFile(filePath, machineUrl, {
    type: "png",
    width: 400,
    margin: 2,
    color: {
      dark: "#000000",
      light: "#FFFFFF",
    },
  });

  return `/qrcodes/${filename}`;
}
