import { ControlNav } from './ControlNav';

export default function ControlRoomLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <ControlNav />
      {children}
    </>
  );
}
