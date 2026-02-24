/** Regex for a valid 6-digit CSS hex color, e.g. #6366f1 */
export const HEX_COLOR_REGEX = /^#[0-9a-fA-F]{6}$/;

/**
 * Returns true if the string is a valid, safe logo URL:
 * - Must use the https: protocol
 * - Must parse as a valid URL
 */
export function isValidLogoUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "https:";
  } catch {
    return false;
  }
}
