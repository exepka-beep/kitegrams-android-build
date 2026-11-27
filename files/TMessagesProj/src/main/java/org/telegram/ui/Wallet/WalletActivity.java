/*
 * KiteGrams — экран «Деньги».
 *
 * Раздел перенесён из исходников JavaGram v2.26-javagram (ресурсы кошелька
 * org.telegram.ui.Wallet), но работает в рабочем APK-конвейере KiteGrams
 * (Telegram Android 12.10.2, workflow build-apk.yml). Полный TON-движок
 * JavaGram 13.x не используется: перенесены ресурсы и визуальная структура
 * Money-экрана — карточка баланса, быстрые действия и список транзакций.
 */
package org.telegram.ui.Wallet;

import android.content.Context;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.ActionBarMenu;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;

public class WalletActivity extends BaseFragment {

    private static final int BLUE = 0xFF3F8CFF;
    private static final int CARD_TOP = 0xFF1E8FFF;
    private static final int CARD_BOTTOM = 0xFF0A5BD8;

    @Override
    public View createView(Context context) {
        actionBar.setBackButtonImage(0);
        actionBar.setAllowOverlayTitle(true);
        actionBar.setTitle("Деньги");

        ActionBarMenu menu = actionBar.createMenu();
        menu.addItem(1, R.drawable.ic_ab_other).setContentDescription("Меню");
        menu.addItem(2, R.drawable.ic_wallet_close).setContentDescription("Закрыть");

        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
            @Override
            public void onItemClick(int id) {
                if (id == -1 || id == 2) {
                    finishFragment();
                } else if (id == 1) {
                    presentFragment(new WalletProfileCardActivity());
                }
            }
        });

        ScrollView scrollView = new ScrollView(context);
        scrollView.setFillViewport(true);
        scrollView.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));

        LinearLayout root = new LinearLayout(context);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(14), dp(14), dp(14), dp(24));
        scrollView.addView(root, new ScrollView.LayoutParams(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));

        root.addView(makeWalletCard(context, false), LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 188, 0, 0, 0, 16));

        TextView section = new TextView(context);
        section.setText("Мои деньги");
        section.setTextColor(BLUE);
        section.setTextSize(13);
        section.setTypeface(medium());
        section.setPadding(dp(4), 0, 0, 0);
        root.addView(section, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, 0, 4, 0, 10));

        LinearLayout actions = new LinearLayout(context);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        actions.setGravity(Gravity.CENTER_VERTICAL);
        root.addView(actions, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 0, 0, 18));

        actions.addView(makeAction(context, R.drawable.jg_wallet_transaction_topup, "Пополнить", new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Toast.makeText(v.getContext(), "Пополнение", Toast.LENGTH_SHORT).show();
            }
        }), LayoutHelper.createLinear(0, LayoutHelper.WRAP_CONTENT, 1f, Gravity.CENTER, 0, 0, 3, 0));
        actions.addView(makeAction(context, R.drawable.jg_wallet_transfer, "Отправить", new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Toast.makeText(v.getContext(), "Отправка", Toast.LENGTH_SHORT).show();
            }
        }), LayoutHelper.createLinear(0, LayoutHelper.WRAP_CONTENT, 1f, Gravity.CENTER, 3, 0, 3, 0));
        actions.addView(makeAction(context, R.drawable.jg_wallet_currency_exchange, "Обмен", new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Toast.makeText(v.getContext(), "Обмен GRAM", Toast.LENGTH_SHORT).show();
            }
        }), LayoutHelper.createLinear(0, LayoutHelper.WRAP_CONTENT, 1f, Gravity.CENTER, 3, 0, 3, 0));
        actions.addView(makeAction(context, R.drawable.jg_wallet_nft, "NFT", new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Toast.makeText(v.getContext(), "Мои NFT", Toast.LENGTH_SHORT).show();
            }
        }), LayoutHelper.createLinear(0, LayoutHelper.WRAP_CONTENT, 1f, Gravity.CENTER, 3, 0, 0, 0));

        TextView txTitle = new TextView(context);
        txTitle.setText("Транзакции");
        txTitle.setTextColor(BLUE);
        txTitle.setTextSize(13);
        txTitle.setTypeface(medium());
        txTitle.setPadding(dp(4), 0, 0, 0);
        root.addView(txTitle, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, 0, 4, 0, 10));

        addTransaction(context, root, "Gradius company (администратор)", "Входящий перевод", "21 нояб в 17:31", "+0,10", R.drawable.jg_wallet_transaction_in);
        addTransaction(context, root, "Gradius company (администратор)", "Исходящий перевод", "21 нояб в 16:40", "−0,10", R.drawable.jg_wallet_transaction_out);
        addTransaction(context, root, "?", "Входящий перевод", "21 нояб в 15:02", "+0,10", R.drawable.jg_wallet_transaction_topup);

        TextView note = new TextView(context);
        note.setText("Транзакции на сумму менее 0,1 GRAM скрыты.");
        note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
        note.setTextSize(12);
        note.setPadding(dp(4), dp(6), dp(4), 0);
        root.addView(note, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));

        fragmentView = scrollView;
        return fragmentView;
    }

    static FrameLayout makeWalletCard(Context context, boolean compact) {
        FrameLayout card = new FrameLayout(context);
        GradientDrawable bg = new GradientDrawable(GradientDrawable.Orientation.TL_BR, new int[] {CARD_TOP, CARD_BOTTOM});
        bg.setCornerRadius(dp(16));
        card.setBackground(bg);

        ImageView diamond = new ImageView(context);
        diamond.setImageResource(R.drawable.jg_wallet_card_diamond);
        card.addView(diamond, LayoutHelper.createFrame(32, 32, Gravity.LEFT | Gravity.TOP, 14, compact ? 38 : 46, 0, 0));

        TextView balance = new TextView(context);
        balance.setText("0,10 GRAM");
        balance.setTextColor(0xFFFFFFFF);
        balance.setTextSize(compact ? 23 : 26);
        balance.setTypeface(medium());
        card.addView(balance, LayoutHelper.createFrame(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.LEFT | Gravity.TOP, 54, compact ? 38 : 46, 0, 0));

        TextView fiat = new TextView(context);
        fiat.setText("$0.10");
        fiat.setTextColor(0xB3FFFFFF);
        fiat.setTextSize(14);
        card.addView(fiat, LayoutHelper.createFrame(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.LEFT | Gravity.TOP, 55, compact ? 70 : 82, 0, 0));

        ImageView gram = new ImageView(context);
        gram.setImageResource(R.drawable.jg_wallet_gram_small);
        card.addView(gram, LayoutHelper.createFrame(14, 14, Gravity.LEFT | Gravity.TOP, 55, compact ? 73 : 85, 0, 0));

        TextView hide = new TextView(context);
        hide.setText("СПРИТАТЬСЯ");
        hide.setTextColor(0xE6FFFFFF);
        hide.setTextSize(12);
        hide.setTypeface(medium());
        card.addView(hide, LayoutHelper.createFrame(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.LEFT | Gravity.BOTTOM, 18, 0, 0, 16));

        FrameLayout qrBox = new FrameLayout(context);
        GradientDrawable qrBg = new GradientDrawable();
        qrBg.setColor(0x2EFFFFFF);
        qrBg.setCornerRadius(dp(12));
        qrBox.setBackground(qrBg);
        ImageView qr = new ImageView(context);
        qr.setImageResource(R.drawable.jg_wallet_card_qr);
        qr.setColorFilter(0xFFFFFFFF);
        qrBox.addView(qr, LayoutHelper.createFrame(20, 20, Gravity.CENTER));
        card.addView(qrBox, LayoutHelper.createFrame(40, 40, Gravity.RIGHT | Gravity.TOP, 0, 16, 14, 0));

        TextView micro = new TextView(context);
        micro.setText("WALLET 4GD2 6Q7U 8R9S 0T1V");
        micro.setTextColor(0x55FFFFFF);
        micro.setTextSize(9);
        micro.setSingleLine(true);
        micro.setRotation(90f);
        card.addView(micro, LayoutHelper.createFrame(110, 14, Gravity.RIGHT | Gravity.TOP, 0, 36, 10, 0));

        return card;
    }

    private static LinearLayout makeAction(Context context, int icon, String label, View.OnClickListener listener) {
        LinearLayout button = new LinearLayout(context);
        button.setOrientation(LinearLayout.VERTICAL);
        button.setGravity(Gravity.CENTER_HORIZONTAL);
        button.setPadding(0, dp(10), 0, dp(10));
        button.setOnClickListener(listener);

        ImageView image = new ImageView(context);
        image.setImageResource(icon);
        image.setColorFilter(BLUE);
        button.addView(image, LayoutHelper.createLinear(24, 24, Gravity.CENTER_HORIZONTAL, 0, 0, 0, 8));

        TextView text = new TextView(context);
        text.setText(label);
        text.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        text.setTextSize(12);
        text.setTypeface(medium());
        button.addView(text, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL));
        return button;
    }

    private static void addTransaction(Context context, LinearLayout parent, String name, String desc, String time, String amount, int icon) {
        LinearLayout row = new LinearLayout(context);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, dp(10), dp(4), dp(10));

        FrameLayout avatarBox = new FrameLayout(context);
        GradientDrawable circle = new GradientDrawable();
        circle.setShape(GradientDrawable.OVAL);
        circle.setColor(0xFFE8F1FF);
        avatarBox.setBackground(circle);
        ImageView avatar = new ImageView(context);
        avatar.setImageResource(icon);
        avatar.setColorFilter(BLUE);
        avatarBox.addView(avatar, LayoutHelper.createFrame(20, 20, Gravity.CENTER));
        row.addView(avatarBox, LayoutHelper.createLinear(40, 40, Gravity.CENTER_VERTICAL, 0, 0, 12, 0));

        LinearLayout texts = new LinearLayout(context);
        texts.setOrientation(LinearLayout.VERTICAL);

        LinearLine topLine = new LinearLine(context);
        TextView nameView = new TextView(context);
        nameView.setText(name);
        nameView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        nameView.setTextSize(15);
        nameView.setSingleLine(true);
        nameView.setEllipsize(android.text.TextUtils.TruncateAt.END);
        topLine.addView(nameView, LayoutHelper.createLinear(0, LayoutHelper.WRAP_CONTENT, 1f, Gravity.CENTER_VERTICAL, 0, 0, 0, 0));

        TextView amountView = new TextView(context);
        amountView.setText(amount);
        amountView.setTextColor(BLUE);
        amountView.setTextSize(15);
        amountView.setTypeface(medium());
        topLine.addView(amountView, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_VERTICAL, 6, 0, 0, 0));

        ImageView gem = new ImageView(context);
        gem.setImageResource(R.drawable.jg_wallet_gram_14);
        gem.setColorFilter(BLUE);
        topLine.addView(gem, LayoutHelper.createLinear(14, 14, Gravity.CENTER_VERTICAL, 4, 0, 0, 0));
        texts.addView(topLine, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));

        TextView descView = new TextView(context);
        descView.setText(desc);
        descView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
        descView.setTextSize(13);
        texts.addView(descView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 3, 0, 0));

        TextView timeView = new TextView(context);
        timeView.setText(time);
        timeView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
        timeView.setTextSize(12);
        texts.addView(timeView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 2, 0, 0));

        row.addView(texts, LayoutHelper.createLinear(0, LayoutHelper.WRAP_CONTENT, 1f, Gravity.CENTER_VERTICAL, 0, 0, 0, 0));
        parent.addView(row, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));
    }

    private static Typeface medium() {
        return AndroidUtilities.getTypeface("fonts/rmedium.ttf");
    }

    private static int dp(int value) {
        return AndroidUtilities.dp(value);
    }

    private static class LinearLine extends LinearLayout {
        LinearLine(Context context) {
            super(context);
            setOrientation(LinearLayout.HORIZONTAL);
            setGravity(Gravity.CENTER_VERTICAL);
        }
    }
}
