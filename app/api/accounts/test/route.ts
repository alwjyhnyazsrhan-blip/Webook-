import { NextRequest, NextResponse } from "next/server";
import { dbStore } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const { id } = await req.json();

    const account = dbStore.getAccountById(id);
    if (!account) {
      return NextResponse.json({ success: false, error: "Account not found" }, { status: 404 });
    }

    // Simulate real Webook token verification & health ping
    const isSuccess = account.status !== "EXPIRED" && account.status !== "DISABLED";
    const latency = Math.floor(45 + Math.random() * 60);

    if (isSuccess) {
      dbStore.updateAccount(id, {
        status: "LOGGED_IN",
        last_used: new Date().toISOString(),
      });

      return NextResponse.json({
        success: true,
        status: "LOGGED_IN",
        latency_ms: latency,
        message: `تم التحقق بنجاح من اتصال جلسة Webook لحساب: ${account.email}`,
        webook_profile: {
          email: account.email,
          phone: account.phone || "+966 50 *** ****",
          wallet_balance: "0.00 ر.س",
          verified: true,
          ip_origin: account.proxy ? "Saudi Arabia (Proxy Res)" : "Direct Cloud",
        },
      });
    } else {
      return NextResponse.json({
        success: false,
        status: account.status,
        message: `فشل التحقق: الحساب بحالة (${account.status}). يرجى تحديث رمز الجلسة أو كوكيز الحماية.`,
      });
    }
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
