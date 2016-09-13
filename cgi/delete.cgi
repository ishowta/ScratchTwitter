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
use DateTime;
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');
require 'utils.cgi';

sub mainpage_operator {
	# Config
	my $MAIN_PAGE_TMPL_PATH = '../tmpl/mainpage.tmpl';
	my $MAIN_PAGE_CGI_PATH = 'mainpage.cgi';

	# Init
	my $CGI = CGI->new();

	# Get cookie
	my $user_name =  HTML::Entities::encode_entities(decode_utf8($CGI->cookie('user_name')));
	my $user_password =  HTML::Entities::encode_entities(decode_utf8($CGI->cookie('user_password')));

	# Get param
	my $tweet_id =  HTML::Entities::encode_entities(decode_utf8($CGI->param('id')));

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->cookie('user_name')) || !(defined $CGI->cookie('user_password')) || !(defined $CGI->param('id'))){
		$status_code = '400';
		$mode = 'fail';
	}else{
		$status_code = '200';
		$mode = 'showPage';
	}
	my @HEADER = (
			-type => 'text/html',
			-charset => "utf-8",
			-status => $status_code
		);

	# Body
	if($mode eq 'showPage'){
		# Connect DBI
		my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',
		{
			mysql_enable_utf8 => 1
		});
		my $sth;
		my $result;
		# Login Check
		$sth = $dbh->prepare('SELECT COUNT(*) FROM user WHERE mail = ? AND password = ?');
		$sth->execute($user_name, $user_password);
		$result = $sth->fetchall_arrayref(+{});
		my $isPasswordDuplicate = $result->[0]->{'COUNT(*)'};
		# パスワードが間違っていたら400
		if($isPasswordDuplicate eq '0'){
			push @HEADER , ('-status', '400');
			print $CGI->header(@HEADER);
			return;
		}else{
			# ユーザーID取得
			$sth = $dbh->prepare('SELECT id FROM user WHERE mail = ? AND password = ?');
			$sth->execute($user_name, $user_password);
			$result = $sth->fetchall_arrayref(+{});
			my $user_id = $result->[0]->{'id'};

			# ツイートが本当にユーザーのものなのかチェック
			$sth = $dbh->prepare('SELECT user_id FROM tweet WHERE id = ?');
			$sth->execute($tweet_id);
			$result = $sth->fetchall_arrayref(+{});
			if(length(@$result) == 1 && $result->[0]->{'user_id'} == $user_id){
				# ツイート削除
				my $dt = DateTime->now(time_zone => 'Asia/Tokyo');
				$sth = $dbh->prepare('DELETE FROM tweet WHERE id = ?');
				$sth->execute($tweet_id);
				# Add location
				push @HEADER , ('-location',$MAIN_PAGE_CGI_PATH);
				print $CGI->header(@HEADER);
				return;
			}else{
				push @HEADER , ('-status', '400');
				print $CGI->header(@HEADER);
				return;
			}
		}
	}elsif($mode eq 'fail'){
		print $CGI->header(@HEADER);
	}

}

mainpage_operator();
