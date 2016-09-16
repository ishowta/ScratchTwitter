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

package Utils;

sub encodeHTMLMulti {
	my $text = shift;
	$text =~ s/(.)/'&#'.ord($1).';'/eg;
	return $text;
}

sub isValidEmail {
	my $user_email = shift;
	return length($user_email) <= 255 && $user_email =~ /^((?!@)[!-~])+@((?!@)[!-~])+$/;
}

sub isValidUserPassword {
	my $password = shift;
	return $password =~ /^[!-~]{8,128}$/;
}

sub isValidTweetText {
	my $tweet_text = shift;
	# 改行を一文字と判断
	$tweet_text =~ s/\r\n/S/g;
	return length($tweet_text) <= 140;
}

sub checkAccount {
	my ($user_name, $user_password) = @_;

	# Login Check
	my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',{mysql_enable_utf8 => 1});
	my $sth = $dbh->prepare('SELECT COUNT(*), id FROM user WHERE mail = ? AND password = ?');
	$sth->execute($user_name, $user_password);
	my $result = $sth->fetchall_arrayref(+{});
	my $isPasswordDuplicate = $result->[0]->{'COUNT(*)'};
	$dbh->disconnect;

	# パスワードが間違っていたら-1
	if($isPasswordDuplicate eq '0'){
		return -1;
	}else{
		return $result->[0]->{'id'};
	}
}

1;