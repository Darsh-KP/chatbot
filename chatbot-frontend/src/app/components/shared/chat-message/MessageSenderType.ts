export type MessageSenderType = 'user' | 'system';

// Function to automatically parse number 0 | 1 to user | system, respectively
export function transformSender(value: number | string | MessageSenderType): MessageSenderType {
  if (value === 0 || value === '0' || value === 'user') {
    return 'user';
  }
  return 'system';
}
