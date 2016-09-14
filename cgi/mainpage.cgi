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
use POSIX 'ceil';
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');
require 'utils.cgi';
require 'timeline.pl';

sub page_operator {
	# Config
	my $MAIN_PAGE_TMPL_PATH = '../tmpl/mainpage.tmpl';
	my $LOGIN_PAGE_TMPL_PATH = '../tmpl/login.tmpl';
	my $LOGIN_PAGE_CGI_PATH = 'login.cgi';

	# Init
	my $CGI = CGI->new();

	# Get cookie
	my $user_name =  decode_utf8($CGI->cookie('user_name'));
	my $user_password =  decode_utf8($CGI->cookie('user_password'));

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->cookie('user_name')) || !(defined $CGI->cookie('user_password'))){
		$status_code = '200';
		$mode = 'jumpLoginPage';
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

		# Login Check
		my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',{mysql_enable_utf8 => 1});
		my $sth = $dbh->prepare('SELECT COUNT(*), id FROM user WHERE mail = ? AND password = ?');
		$sth->execute($user_name, $user_password);
		my $result = $sth->fetchall_arrayref(+{});
		my $isPasswordDuplicate = $result->[0]->{'COUNT(*)'};
		$dbh->disconnect;
		# パスワードが間違っていたら400
		if($isPasswordDuplicate eq '0'){
			push @HEADER , ('-status', '400');
			print $CGI->header(@HEADER);
			return;
		}
		my $user_id = $result->[0]->{'id'};

		### メインページ表示

		# Load tmpl
		my $this_page_tmpl = HTML::Template->new(filename => $MAIN_PAGE_TMPL_PATH,utf8 => 1);

		# Make TimeLine
		my $timeline_tmpl = makeTimeLine($CGI, '', [], $user_id);
		$this_page_tmpl->param('TIMELINE_TMPL' => $timeline_tmpl->output);

		# Set Header
		print $CGI->header(@HEADER), $this_page_tmpl->output;

	}elsif($mode eq 'jumpLoginPage'){
		# Add location
		push @HEADER , ('-location',$LOGIN_PAGE_CGI_PATH);

		# Set Header
		print $CGI->header(@HEADER);
	}

}

page_operator();
