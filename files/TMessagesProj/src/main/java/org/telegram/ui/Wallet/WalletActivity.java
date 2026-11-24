/*
 * KiteGrams — нативный экран «Деньги».
 * Сделан в стиле оригинального Telegram: боковое меню -> Деньги.
 * Пакет Separation: не зависит от классов Wallet из 13.x, поэтому
 * собирается поверх закреплённого дерева 12.10.1 (LAYER 229).
 */
package org.telegram.ui.Wallet;

import android.content.Context;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;

public class WalletActivity extends BaseFragment {

    public static final String WALLET_URL = "https://kitegrams.duckdns.org/wallet/";

    @Override
    public View createView(Context context) {
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setAllowOverlayTitle(true);
        actionBar.setTitle("Деньги");
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
            @Override
            public void onItemClick(int id) {
                if (id == -1) {
                    finishFragment();
                }
            }
        });

        ScrollView scrollView = new ScrollView(context);
        scrollView.setFillViewport(true);
        scrollView.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));

        LinearLayout root = new LinearLayout(context);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(AndroidUtilities.dp(16), AndroidUtilities.dp(16), AndroidUtilities.dp(16), AndroidUtilities.dp(28));
        scrollView.addView(root, new ScrollView.LayoutParams(ScrollView.LayoutParams.MATCH_PARENT, ScrollView.LayoutParams.WRAP_CONTENT));

        // --- карточка баланса ---
        GradientDrawable card = new GradientDrawable(GradientDrawable.Orientation.TL_BR, new int[]{0xFF2E7CF6, 0xFF7B4DFF});
        card.setCornerRadius(AndroidUtilities.dp(18));
        LinearLayout cardLayout = new LinearLayout(context);
        cardLayout.setOrientation(LinearLayout.VERTICAL);
        cardLayout.setBackground(card);
        cardLayout.setPadding(AndroidUtilities.dp(20), AndroidUtilities.dp(22), AndroidUtilities.dp(20), AndroidUtilities.dp(22));
        root.addView(cardLayout, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 0, 0, 18));

        TextView cardLabel = new TextView(context);
        cardLabel.setText("Баланс");
        cardLabel.setTextColor(0xCCFFFFFF);
        cardLabel.setTextSize(14);
        cardLayout.addView(cardLabel);

        TextView cardAmount = new TextView(context);
        cardAmount.setText("0 TON");
        cardAmount.setTextColor(0xFFFFFFFF);
        cardAmount.setTextSize(30);
        cardAmount.setTypeface(Typeface.DEFAULT_BOLD);
        cardLayout.addView(cardAmount, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, 0, 6, 0, 0));

        TextView cardSub = new TextView(context);
        cardSub.setText("Кошелёк KiteGrams · TON");
        cardSub.setTextColor(0xB3FFFFFF);
        cardSub.setTextSize(13);
        cardLayout.addView(cardSub, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, 0, 6, 0, 0));

        // --- кнопки действий ---
        LinearLayout actions = new LinearLayout(context);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        root.addView(actions, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 0, 0, 20));

        TextView topUp = makeButton(context, "Пополнить", true, new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openWallet();
            }
        });
        TextView withdraw = makeButton(context, "Вывести", false, new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openWallet();
            }
        });
        actions.addView(topUp, LayoutHelper.createLinear(0, 46, 1f, Gravity.START, 0, 0, 6, 0));
        actions.addView(withdraw, LayoutHelper.createLinear(0, 46, 1f, Gravity.END, 6, 0, 0, 0));

        // --- заголовок истории ---
        TextView historyTitle = new TextView(context);
        historyTitle.setText("История");
        historyTitle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        historyTitle.setTextSize(17);
        historyTitle.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(historyTitle, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, 0, 0, 0, 10));

        LinearLayout history = new LinearLayout(context);
        history.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable historyBg = new GradientDrawable();
        historyBg.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        historyBg.setCornerRadius(AndroidUtilities.dp(12));
        history.setBackground(historyBg);
        history.setPadding(AndroidUtilities.dp(14), AndroidUtilities.dp(4), AndroidUtilities.dp(14), AndroidUtilities.dp(4));
        root.addView(history, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));

        addTransaction(context, history, "Пополнение", "Сегодня, 12:40", "+ 5 TON", 0xFF2EAA6B, true);
        addTransaction(context, history, "Перевод", "Вчера, 18:12", "− 1.5 TON", 0xFFE6762E, false);
        addTransaction(context, history, "Подарок", "23 ноября, 09:03", "+ 2 TON", 0xFF2EAA6B, true);

        TextView note = new TextView(context);
        note.setText("Показаны примеры операций. Актуальный баланс и история — в веб-кошельке.");
        note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
        note.setTextSize(12);
        note.setGravity(Gravity.CENTER);
        root.addView(note, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 12, 0, 0));

        TextView openWeb = new TextView(context);
        openWeb.setText("Открыть кошелёк");
        openWeb.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        openWeb.setTextSize(15);
        openWeb.setGravity(Gravity.CENTER);
        openWeb.setPadding(0, AndroidUtilities.dp(14), 0, AndroidUtilities.dp(8));
        openWeb.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openWallet();
            }
        });
        root.addView(openWeb, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));

        fragmentView = scrollView;
        return fragmentView;
    }

    private TextView makeButton(Context context, String text, boolean primary, View.OnClickListener listener) {
        TextView button = new TextView(context);
        button.setText(text);
        button.setGravity(Gravity.CENTER);
        button.setTextSize(14);
        button.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(primary ? Theme.getColor(Theme.key_dialogButton) : Theme.getColor(Theme.key_windowBackgroundWhite));
        bg.setStroke(AndroidUtilities.dp(1), Theme.getColor(Theme.key_divider));
        bg.setCornerRadius(AndroidUtilities.dp(12));
        button.setBackground(bg);
        button.setTextColor(primary ? 0xFFFFFFFF : Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        button.setOnClickListener(listener);
        return button;
    }

    private void addTransaction(Context context, LinearLayout parent, String title, String date, String amount, int color, boolean income) {
        LinearLayout row = new LinearLayout(context);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, AndroidUtilities.dp(11), 0, AndroidUtilities.dp(11));

        GradientDrawable circle = new GradientDrawable();
        circle.setShape(GradientDrawable.OVAL);
        circle.setColor(income ? 0x222EAA6B : 0x22E6762E);
        TextView icon = new TextView(context);
        icon.setText(income ? "↓" : "↑");
        icon.setGravity(Gravity.CENTER);
        icon.setTextColor(color);
        icon.setTextSize(18);
        icon.setBackground(circle);
        row.addView(icon, LayoutHelper.createLinear(38, 38, Gravity.CENTER_VERTICAL, 0, 0, 12, 0));

        LinearLayout texts = new LinearLayout(context);
        texts.setOrientation(LinearLayout.VERTICAL);
        TextView t = new TextView(context);
        t.setText(title);
        t.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        t.setTextSize(15);
        texts.addView(t);
        TextView d = new TextView(context);
        d.setText(date);
        d.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
        d.setTextSize(12);
        texts.addView(d);
        row.addView(texts, LayoutHelper.createLinear(0, LayoutHelper.WRAP_CONTENT, 1f, Gravity.CENTER_VERTICAL));

        TextView a = new TextView(context);
        a.setText(amount);
        a.setTextColor(color);
        a.setTextSize(15);
        a.setTypeface(Typeface.DEFAULT_BOLD);
        row.addView(a, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_VERTICAL));

        parent.addView(row, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));
    }

    private void openWallet() {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(WALLET_URL));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            if (getParentActivity() != null) {
                getParentActivity().startActivity(intent);
            }
        } catch (Exception e) {
            if (getParentActivity() != null) {
                Toast.makeText(getParentActivity(), "Не удалось открыть кошелёк", Toast.LENGTH_SHORT).show();
            }
        }
    }
}
