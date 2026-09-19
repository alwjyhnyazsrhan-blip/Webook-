import { NextRequest, NextResponse } from "next/server";
import { dbStore } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");

    if (id) {
      const account = dbStore.getAccountById(id);
      if (!account) {
        return NextResponse.json({ success: false, error: "Account not found" }, { status: 404 });
      }
      return NextResponse.json({ success: true, account });
    }

    const accounts = dbStore.getAccounts();
    return NextResponse.json({
      success: true,
      total: accounts.length,
      accounts,
    });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Check if batch import
    if (Array.isArray(body.accounts)) {
      const created = dbStore.batchImportAccounts(body.accounts);
      return NextResponse.json({
        success: true,
        message: `تم استيراد ${created.length} حساب بنجاح`,
        count: created.length,
        accounts: dbStore.getAccounts(),
      });
    }

    // Single account creation
    if (!body.email) {
      return NextResponse.json({ success: false, error: "البريد الإلكتروني مطلوب" }, { status: 400 });
    }

    const newAcc = dbStore.createAccount({
      email: body.email.trim(),
      name: body.name?.trim() || body.email.split("@")[0],
      phone: body.phone?.trim() || "+966 50 000 0000",
      password: body.password || "••••••••••••",
      token: body.token?.trim() || `wbk_live_${Math.random().toString(36).substring(2, 16)}`,
      status: body.status || "ACTIVE",
      proxy: body.proxy?.trim() || "185.193.64.10:8080",
      max_seats: Number(body.max_seats) || 4,
      notes: body.notes?.trim() || "",
    });

    return NextResponse.json({
      success: true,
      message: "تم إضافة حساب Webook بنجاح",
      account: newAcc,
      accounts: dbStore.getAccounts(),
    });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    const body = await req.json();
    const { id, ...updates } = body;

    if (!id) {
      return NextResponse.json({ success: false, error: "Account ID is required" }, { status: 400 });
    }

    const updated = dbStore.updateAccount(id, updates);
    if (!updated) {
      return NextResponse.json({ success: false, error: "Account not found" }, { status: 404 });
    }

    return NextResponse.json({
      success: true,
      message: `تم تحديث الحساب (${updated.email}) بنجاح`,
      account: updated,
      accounts: dbStore.getAccounts(),
    });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");

    if (!id) {
      return NextResponse.json({ success: false, error: "Account ID is required" }, { status: 400 });
    }

    const deleted = dbStore.deleteAccount(id);
    if (!deleted) {
      return NextResponse.json({ success: false, error: "Account not found" }, { status: 404 });
    }

    return NextResponse.json({
      success: true,
      message: "تم حذف الحساب بنجاح",
      accounts: dbStore.getAccounts(),
    });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
