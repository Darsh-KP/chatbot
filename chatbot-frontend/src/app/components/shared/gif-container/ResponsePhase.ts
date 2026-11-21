export type ResponsePhase =
  | 'greeting'
  | 'thinking'
  | 'responseSuccess'
  | 'responseFailure'
  | 'noAnimation';

export function getGifFilePath(responsePhase: ResponsePhase): string {
  switch (responsePhase) {
    case 'greeting':
      return '/greeting.gif';
    case 'thinking':
      return '/thinking.gif';
    case 'responseSuccess':
      return '/responseSuccess.gif';
    case 'responseFailure':
      return '/responseFailure.gif';
    case 'noAnimation':
      return '';
  }
}
