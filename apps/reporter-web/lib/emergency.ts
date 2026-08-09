export interface EmergencyResult {
  country: { name: string; code: string };
  police: string[];
  fire: string[];
  ambulance: string[];
  dispatch: string[];
  member112: boolean;
  source: 'live' | 'cached';
  fetchedAt: string;
}

export interface DetectedLocation {
  city: string;
  countryName: string;
  countryCode: string;
  method: 'gps' | 'ip' | 'manual';
}

export interface EmergencyError {
  error: string;
}
