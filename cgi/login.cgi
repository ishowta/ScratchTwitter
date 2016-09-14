#!/usr/bin/perl

use strict;
use utf8;
use CGI;
use CGI::Cookie;
use DBI;
use lib ('/home/takahashi/perl/local/lib/perl5');
use HTML::Template;
use HTML::Entities;
use Encode;
use Data::Dumper;
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');
require 'utils.cgi';

sub login_operator {
	# Config
	my $LOGIN_PAGE_TMPL_PATH = '../tmpl/login.tmpl';
	my $MAIN_PAGE_CGI_PATH = 'mainpage.cgi';
	my $invalidUserNameMessage = 'メールアドレスの書式が無効です。';
	my $invalidUserPasswordMessage = 'パスワードの書式が無効です。8文字以上128文字以内の半角英数記号で入力してください';
	my $faildLoginMessage = 'パスワードが間違っています。';

	# Init
	my $CGI = CGI->new();

	# Get param
	my $user_name = decode_utf8($CGI->param('name'));
	my $user_password = decode_utf8($CGI->param('password'));

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->param('name')) || !(defined $CGI->param('password'))){
		$status_code = '200';
		$mode = 'showPage';
	}else{
		$status_code = '200';
		$mode = 'tryLogin';
	}
	my @HEADER = (
			-type => 'text/html',
			-charset => "utf-8",
			-status => $status_code
		);

	# Body
	if($mode eq 'showPage'){
		# Load tmpl
		my $login_page_tmpl = HTML::Template->new(
			filename => $LOGIN_PAGE_TMPL_PATH,
			utf8 => 1
		);

		# Push placeholder
		my $input_tag = '<input type="email" name="name" class="form-control" id="emailInput" placeholder="xxx@xxx.com">';
		$login_page_tmpl->param(INPUT_BIGIN_TAG_WITH_EMAIL_PLACEHOLDER => $input_tag);

		# Output tmpl
		print $CGI->header(@HEADER), $login_page_tmpl->output;
	}elsif($mode eq 'tryLogin'){

		my $isValidUserName = Utils::isValidEmail($user_name);
		my $isValidUserPassword = Utils::isValidUserPassword($user_password);

		if($isValidUserName == 0 || $isValidUserPassword == 0){
			# Load tmpl
			my $login_page_tmpl = HTML::Template->new(
				filename => $LOGIN_PAGE_TMPL_PATH,
				utf8 => 1
			);

			if($isValidUserName == 0){
				# Attach tmpl
				$login_page_tmpl->param(IS_EMAIL_ERROR => 1);
				$login_page_tmpl->param(InvalidUserNameMessage => HTML::Entities::encode_entities($invalidUserNameMessage));
			}
			if($isValidUserPassword == 0){
				$login_page_tmpl->param(IS_PASSWORD_ERROR => 1);
				# Attach tmpl
				$login_page_tmpl->param(InvalidUserPasswordMessage => HTML::Entities::encode_entities($invalidUserPasswordMessage));
			}

			# Push placeholder
			my $input_tag = '<input type="email" name="name" class="form-control" id="emailInput" value="'.HTML::Entities::encode_entities(encode_utf8($user_name)).'">';
			$login_page_tmpl->param(INPUT_BIGIN_TAG_WITH_EMAIL_PLACEHOLDER => $input_tag);

			print $CGI->header(@HEADER), $login_page_tmpl->output;
		}else{
			# Connect DBI
			my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',
			{
				mysql_enable_utf8 => 1
			});
			my $sth;
			my $result;
			# 名前の重複をチェック
			$sth = $dbh->prepare('SELECT COUNT(*) FROM user WHERE mail = ?');
			$sth->execute($user_name);
			$result = $sth->fetchall_arrayref(+{});
			my $isNameDuplicate = $result->[0]->{'COUNT(*)'};
			if($isNameDuplicate eq '0'){
				# 重複がないので新しく追加する
				$sth = $dbh->prepare('INSERT INTO user (mail, password) VALUES (?, ?)');
				$sth->execute($user_name, $user_password);
			}else{
				# 重複があったので、パスワードが一致するかチェック
				$sth = $dbh->prepare('SELECT COUNT(*) FROM user WHERE mail = ? AND password = ?');
				$sth->execute($user_name, $user_password);
				$result = $sth->fetchall_arrayref(+{});
				my $isPasswordDuplicate = $result->[0]->{'COUNT(*)'};
				# パスワードが間違っていたらエラーを返して終わり
				if($isPasswordDuplicate eq '0'){
					# Load tmpl
					my $login_page_tmpl = HTML::Template->new(
						filename => $LOGIN_PAGE_TMPL_PATH,
						utf8 => 1
					);
					# Attach tmpl
					$login_page_tmpl->param(IS_PASSWORD_ERROR => 1);
					$login_page_tmpl->param(FaildLoginMessage => HTML::Entities::encode_entities($faildLoginMessage));

					# Push placeholder
					my $input_tag = '<input type="email" name="name" class="form-control" id="emailInput" value="'.HTML::Entities::encode_entities(encode_utf8($user_name)).'">';
					$login_page_tmpl->param(INPUT_BIGIN_TAG_WITH_EMAIL_PLACEHOLDER => $input_tag);

					print $CGI->header(@HEADER), $login_page_tmpl->output;
					return;
				}
			}
			# ログインに成功したのでメインページに飛ばす
			my $cookie_user_name = new CGI::Cookie(-name=>'user_name',-value=>$user_name);
			my $cookie_user_password = new CGI::Cookie(-name=>'user_password',-value=>$user_password);
			# Add cookie
			push @HEADER , ('-cookie',[$cookie_user_name,$cookie_user_password]);
			# Add location
			push @HEADER , ('-location',$MAIN_PAGE_CGI_PATH);
			# Set header
			print $CGI->header(@HEADER);
			return;
		}
	}
}

login_operator();
