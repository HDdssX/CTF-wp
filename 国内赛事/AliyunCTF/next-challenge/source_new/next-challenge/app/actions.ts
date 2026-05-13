'use server'
export async function Hello(input: string): Promise<string> {
  return `hello ${input}!`;
}

export async function GetSource(): Promise<string> {
  // read /source-3527c84d-2ecc-4c76-9d83-7e83138c19a8.zip
  return "";
}