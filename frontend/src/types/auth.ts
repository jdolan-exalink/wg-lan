export interface User {
  id: number;
  username: string;
  must_change_password: boolean;
  onboarding_completed: boolean;
  is_admin: boolean;
}
