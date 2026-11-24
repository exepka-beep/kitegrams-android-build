/*
 * KiteGrams — превью карточки «Деньги» как в профиле Telegram.
 */
package org.telegram.ui.Wallet;

import android.content.Context;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;

public class WalletProfileCardActivity extends BaseFragment {

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
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(24), dp(36), dp(24), dp(36));
        scrollView.addView(root, new ScrollView.LayoutParams(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));

        TextView info = new TextView(context);
        info.setText("Ваш баланс — открытая\nинформация в силу\nпрозрачности блокчейна.");
        info.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
        info.setTextSize(14);
        info.setGravity(Gravity.CENTER);
        info.setLineSpacing(dp(2), 1f);
        root.addView(info, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 0, 0, 28));

        root.addView(WalletActivity.makeWalletCard(context, true), LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 154));

        TextView go = new TextView(context);
        go.setText("Перейти к моим Деньгам");
        go.setGravity(Gravity.CENTER);
        go.setTextColor(0xFFFFFFFF);
        go.setTextSize(14);
        Typeface medium = AndroidUtilities.getTypeface("fonts/rmedium.ttf");
        go.setTypeface(medium);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(0xFF3FAE6E);
        bg.setCornerRadius(dp(22));
        go.setBackground(bg);
        go.setPadding(dp(18), dp(11), dp(18), dp(11));
        go.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                presentFragment(new WalletActivity());
            }
        });
        root.addView(go, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL, 0, 26, 0, 0));

        fragmentView = scrollView;
        return fragmentView;
    }

    private static int dp(int value) {
        return AndroidUtilities.dp(value);
    }
}
