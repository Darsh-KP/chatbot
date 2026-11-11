export type ResponsePhase = 'greeting' | 'thinking' | 'responseSuccess' | 'responseFailed' | 'noAnimation';

export function getGifFilePath(responsePhase: ResponsePhase) {
  switch (responsePhase) {
    case 'greeting':
      return 'greeting.gif';
    case 'thinking':
      return 'thinking.gif';
    case 'responseSuccess':
      return 'responseSuccess.gif';
    case 'responseFailed':
      return 'responseFailed.gif';
    case 'noAnimation':
      return '';
  }
}
