export default function VerifyRequestPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
        <div className="text-5xl mb-4">📧</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Check your email</h2>
        <p className="text-gray-600">
          A magic link has been sent to your email address. Click it to verify
          your email and sign in.
        </p>
        <p className="text-gray-500 text-sm mt-4">
          If you don&apos;t see it, check your spam folder.
        </p>
      </div>
    </div>
  );
}
